from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.utils import timezone
from member.tier_logic import sync_member_tier
# new
import hashlib


def login_required_staf(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_email'):
            return redirect('login')
        if request.session.get('role') != 'staf':
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def get_laporan_filters(request):
    return {
        'tab': request.GET.get('tab', 'riwayat'),
        'tipe': request.GET.get('tipe', '').strip(),
        'member': request.GET.get('member', '').strip(),
        'tgl_dari': request.GET.get('tgl_dari', '').strip(),
        'tgl_sampai': request.GET.get('tgl_sampai', '').strip(),
    }


def get_laporan_stats():
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    with connection.cursor() as c:
        c.execute("SELECT COALESCE(SUM(total_miles), 0) FROM member")
        total_miles_beredar = c.fetchone()[0] or 0

    with connection.cursor() as c:
        c.execute("""
            SELECT COALESCE(SUM(h.miles), 0)
            FROM redeem r
            JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah
            WHERE r.timestamp >= %s
        """, [month_start])
        total_redeem_bulan_ini = c.fetchone()[0] or 0

    with connection.cursor() as c:
        c.execute("""
            SELECT COALESCE(SUM(
                CASE cm.kelas_kabin
                    WHEN 'Economy' THEN 500
                    WHEN 'Business' THEN 1000
                    WHEN 'First' THEN 2000
                    ELSE 500
                END
            ), 0)
            FROM claim_missing_miles cm
            WHERE cm.status_penerimaan = 'Disetujui'
        """)
        total_klaim_disetujui = c.fetchone()[0] or 0

    return {
        'total_miles_beredar': total_miles_beredar,
        'total_redeem_bulan_ini': total_redeem_bulan_ini,
        'total_klaim_disetujui': total_klaim_disetujui,
    }


def get_laporan_transactions(filters):
    query = """
        WITH transaksi AS (
            SELECT
                'Transfer' AS tipe,
                p.first_mid_name || ' ' || p.last_name AS member_nama,
                t.email_member_1 AS member_email,
                -t.jumlah AS miles,
                t.timestamp AS waktu,
                TRUE AS bisa_hapus,
                'transfer' AS delete_type,
                t.email_member_1 AS key_one,
                t.email_member_2 AS key_two,
                TO_CHAR(t.timestamp, 'YYYY-MM-DD"T"HH24:MI:SS.US') AS key_three
            FROM transfer t
            JOIN pengguna p ON t.email_member_1 = p.email

            UNION ALL

            SELECT
                'Redeem',
                p.first_mid_name || ' ' || p.last_name,
                r.email_member,
                -h.miles,
                r.timestamp,
                TRUE,
                'redeem',
                r.email_member,
                r.kode_hadiah,
                TO_CHAR(r.timestamp, 'YYYY-MM-DD"T"HH24:MI:SS.US')
            FROM redeem r
            JOIN pengguna p ON r.email_member = p.email
            JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah

            UNION ALL

            SELECT
                'Package',
                p.first_mid_name || ' ' || p.last_name,
                mp.email_member,
                amp.jumlah_award_miles,
                mp.timestamp,
                TRUE,
                'package',
                mp.email_member,
                mp.id_award_miles_package,
                TO_CHAR(mp.timestamp, 'YYYY-MM-DD"T"HH24:MI:SS.US')
            FROM member_award_miles_package mp
            JOIN pengguna p ON mp.email_member = p.email
            JOIN award_miles_package amp ON mp.id_award_miles_package = amp.id

            UNION ALL

            SELECT
                'Klaim',
                p.first_mid_name || ' ' || p.last_name,
                cm.email_member,
                CASE cm.kelas_kabin
                    WHEN 'Economy' THEN 500
                    WHEN 'Business' THEN 1000
                    WHEN 'First' THEN 2000
                    ELSE 500
                END,
                cm.timestamp,
                FALSE,
                'claim',
                cm.email_member,
                COALESCE(cm.id::text, ''),
                TO_CHAR(cm.timestamp, 'YYYY-MM-DD"T"HH24:MI:SS.US')
            FROM claim_missing_miles cm
            JOIN pengguna p ON cm.email_member = p.email
            WHERE cm.status_penerimaan = 'Disetujui'
        )
        SELECT *
        FROM transaksi
        WHERE 1=1
    """
    params = []

    if filters['tipe']:
        query += " AND tipe = %s"
        params.append(filters['tipe'])

    if filters['member']:
        query += " AND (member_nama ILIKE %s OR member_email ILIKE %s)"
        keyword = f"%{filters['member']}%"
        params.extend([keyword, keyword])

    if filters['tgl_dari']:
        query += " AND waktu::date >= %s"
        params.append(filters['tgl_dari'])

    if filters['tgl_sampai']:
        query += " AND waktu::date <= %s"
        params.append(filters['tgl_sampai'])

    query += " ORDER BY waktu DESC"

    with connection.cursor() as c:
        c.execute(query, params)
        rows = c.fetchall()

    transactions = []
    for row in rows:
        transactions.append({
            'tipe': row[0],
            'member_nama': row[1],
            'member_email': row[2],
            'miles': row[3],
            'waktu': row[4],
            'bisa_hapus': row[5],
            'delete_type': row[6],
            'key_one': row[7],
            'key_two': row[8],
            'key_three': row[9],
        })

    return transactions


def get_top_member_data():
    with connection.cursor() as c:
        c.execute("""
            SELECT
                p.first_mid_name || ' ' || p.last_name AS member_nama,
                m.email,
                COALESCE(m.total_miles, 0) AS total_miles,
                (
                    COALESCE((SELECT COUNT(*) FROM transfer t WHERE t.email_member_1 = m.email), 0) +
                    COALESCE((SELECT COUNT(*) FROM redeem r WHERE r.email_member = m.email), 0) +
                    COALESCE((SELECT COUNT(*) FROM member_award_miles_package mp WHERE mp.email_member = m.email), 0) +
                    COALESCE((SELECT COUNT(*) FROM claim_missing_miles cm WHERE cm.email_member = m.email AND cm.status_penerimaan = 'Disetujui'), 0)
                ) AS jumlah_transaksi
            FROM member m
            JOIN pengguna p ON m.email = p.email
            ORDER BY total_miles DESC, jumlah_transaksi DESC, member_nama ASC
            LIMIT 5
        """)
        top_total_miles_rows = c.fetchall()

    with connection.cursor() as c:
        c.execute("""
            SELECT
                p.first_mid_name || ' ' || p.last_name AS member_nama,
                t.email_member_1 AS member_email,
                COUNT(*) AS jumlah_transfer,
                COALESCE(SUM(t.jumlah), 0) AS total_miles_transfer
            FROM transfer t
            JOIN pengguna p ON t.email_member_1 = p.email
            GROUP BY member_nama, member_email
            ORDER BY jumlah_transfer DESC, total_miles_transfer DESC, member_nama ASC
            LIMIT 5
        """)
        top_transfer_rows = c.fetchall()

    with connection.cursor() as c:
        c.execute("""
            SELECT
                p.first_mid_name || ' ' || p.last_name AS member_nama,
                r.email_member AS member_email,
                COUNT(*) AS jumlah_redeem,
                COALESCE(SUM(h.miles), 0) AS total_miles_redeem
            FROM redeem r
            JOIN pengguna p ON r.email_member = p.email
            JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah
            GROUP BY member_nama, member_email
            ORDER BY jumlah_redeem DESC, total_miles_redeem DESC, member_nama ASC
            LIMIT 5
        """)
        top_redeem_rows = c.fetchall()

    return {
        'top_total_miles': [{
            'ranking': index + 1,
            'member_nama': row[0],
            'member_email': row[1],
            'total_miles': row[2],
            'jumlah_transaksi': row[3],
        } for index, row in enumerate(top_total_miles_rows)],
        'top_transfer': [{
            'ranking': index + 1,
            'member_nama': row[0],
            'member_email': row[1],
            'jumlah_transfer': row[2],
            'total_miles_transfer': row[3],
        } for index, row in enumerate(top_transfer_rows)],
        'top_redeem': [{
            'ranking': index + 1,
            'member_nama': row[0],
            'member_email': row[1],
            'jumlah_redeem': row[2],
            'total_miles_redeem': row[3],
        } for index, row in enumerate(top_redeem_rows)],
    }


@login_required_staf
def laporan_transaksi(request):
    filters = get_laporan_filters(request)

    if filters['tab'] not in ['riwayat', 'top-member']:
        filters['tab'] = 'riwayat'

    context = {
        'filters': filters,
        'stats': get_laporan_stats(),
        'transactions': get_laporan_transactions(filters),
        'top_members': get_top_member_data(),
        'tipe_options': ['Transfer', 'Redeem', 'Package', 'Klaim'],
        'current_url': request.get_full_path(),
    }
    return render(request, 'staf/laporan_transaksi.html', context)


@login_required_staf
def laporan_transaksi_hapus(request):
    if request.method != 'POST':
        return redirect('laporan_transaksi')

    delete_type = request.POST.get('delete_type', '').strip()
    key_one = request.POST.get('key_one', '').strip()
    key_two = request.POST.get('key_two', '').strip()
    key_three = request.POST.get('key_three', '').strip()
    next_url = request.POST.get('next_url', '').strip() or '/laporan/'

    if delete_type not in ['transfer', 'redeem', 'package']:
        messages.error(request, 'Tipe transaksi tidak dapat dihapus.')
        return redirect(next_url)

    try:
        with connection.cursor() as c:
            if delete_type == 'transfer':
                c.execute("""
                    DELETE FROM transfer
                    WHERE email_member_1 = %s
                      AND email_member_2 = %s
                      AND timestamp = %s::timestamp
                """, [key_one, key_two, key_three])
            elif delete_type == 'redeem':
                c.execute("""
                    DELETE FROM redeem
                    WHERE email_member = %s
                      AND kode_hadiah = %s
                      AND timestamp = %s::timestamp
                """, [key_one, key_two, key_three])
            else:
                c.execute("""
                    DELETE FROM member_award_miles_package
                    WHERE email_member = %s
                      AND id_award_miles_package = %s
                      AND timestamp = %s::timestamp
                """, [key_one, key_two, key_three])

            if c.rowcount == 0:
                messages.error(request, 'Riwayat transaksi tidak ditemukan atau sudah terhapus.')
            else:
                messages.success(request, 'Riwayat transaksi berhasil dihapus permanen.')
    except Exception as e:
        messages.error(request, f'Gagal menghapus riwayat transaksi: {e}')

    return redirect(next_url)


# FITUR 9

def get_klaim_list_staf(status_filter='', maskapai_filter='', tgl_dari='', tgl_sampai=''):
    query = """
        SELECT cm.id,
               p.first_mid_name || ' ' || p.last_name AS nama_member,
               cm.email_member,
               mk.nama_maskapai,
               ba.iata_code, ba.nama AS bandara_asal,
               bt.iata_code, bt.nama AS bandara_tujuan,
               cm.tanggal_penerbangan,
               cm.flight_number,
               cm.kelas_kabin,
               cm.timestamp,
               cm.status_penerimaan,
               cm.nomor_tiket,
               cm.pnr
        FROM claim_missing_miles cm
        JOIN member m ON cm.email_member = m.email
        JOIN pengguna p ON m.email = p.email
        JOIN maskapai mk ON cm.maskapai = mk.kode_maskapai
        JOIN bandara ba ON cm.bandara_asal = ba.iata_code
        JOIN bandara bt ON cm.bandara_tujuan = bt.iata_code
        WHERE 1=1
    """
    params = []

    if status_filter:
        query += " AND cm.status_penerimaan = %s"
        params.append(status_filter)

    if maskapai_filter:
        query += " AND cm.maskapai = %s"
        params.append(maskapai_filter)

    if tgl_dari:
        query += " AND cm.timestamp::date >= %s"
        params.append(tgl_dari)

    if tgl_sampai:
        query += " AND cm.timestamp::date <= %s"
        params.append(tgl_sampai)

    query += " ORDER BY cm.timestamp DESC"

    with connection.cursor() as c:
        c.execute(query, params)
        rows = c.fetchall()

    return [{
        'id':                  r[0],
        'nama_member':         r[1],
        'email_member':        r[2],
        'maskapai':            r[3],
        'bandara_asal_code':   r[4],
        'bandara_asal_nama':   r[5],
        'bandara_tujuan_code': r[6],
        'bandara_tujuan_nama': r[7],
        'tanggal_penerbangan': r[8],
        'flight_number':       r[9],
        'kelas_kabin':         r[10],
        'timestamp':           r[11],
        'status':              r[12],
        'nomor_tiket':         r[13],
        'pnr':                 r[14],
    } for r in rows]


@login_required_staf
def klaim_list_staf(request):
    status_filter   = request.GET.get('status', '')
    maskapai_filter = request.GET.get('maskapai', '')
    tgl_dari        = request.GET.get('tgl_dari', '')
    tgl_sampai      = request.GET.get('tgl_sampai', '')
    is_ajax         = request.GET.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    klaim_data = get_klaim_list_staf(status_filter, maskapai_filter, tgl_dari, tgl_sampai)

    with connection.cursor() as c:
        c.execute("SELECT kode_maskapai, nama_maskapai FROM maskapai ORDER BY nama_maskapai")
        maskapai_list = [{'kode': r[0], 'nama': r[1]} for r in c.fetchall()]

    context = {
        'klaim_list':      klaim_data,
        'maskapai_list':   maskapai_list,
        'status_filter':   status_filter,
        'maskapai_filter': maskapai_filter,
        'tgl_dari':        tgl_dari,
        'tgl_sampai':      tgl_sampai,
    }

    if is_ajax:
        return render(request, 'staf/klaim_table_partial_staf.html', context)

    return render(request, 'staf/klaim_list_staf.html', context)


@login_required_staf
def klaim_proses(request, id):
    email_staf = request.session['user_email']

    with connection.cursor() as c:
        c.execute("""
            SELECT cm.id, cm.email_member, cm.status_penerimaan,
                   p.first_mid_name || ' ' || p.last_name AS nama_member,
                   mk.nama_maskapai,
                   ba.iata_code, bt.iata_code,
                   cm.flight_number, cm.kelas_kabin, cm.tanggal_penerbangan
            FROM claim_missing_miles cm
            JOIN member m ON cm.email_member = m.email
            JOIN pengguna p ON m.email = p.email
            JOIN maskapai mk ON cm.maskapai = mk.kode_maskapai
            JOIN bandara ba ON cm.bandara_asal = ba.iata_code
            JOIN bandara bt ON cm.bandara_tujuan = bt.iata_code
            WHERE cm.id = %s
        """, [id])
        row = c.fetchone()

    if not row:
        messages.error(request, 'Klaim tidak ditemukan.')
        return redirect('kelola_klaim')

    klaim = {
        'id':                  row[0],
        'email_member':        row[1],
        'status':              row[2],
        'nama_member':         row[3],
        'maskapai':            row[4],
        'bandara_asal':        row[5],
        'bandara_tujuan':      row[6],
        'flight_number':       row[7],
        'kelas_kabin':         row[8],
        'tanggal_penerbangan': row[9],
    }

    if klaim['status'] != 'Menunggu':
        messages.error(request, 'Klaim ini sudah diproses sebelumnya.')
        return redirect('kelola_klaim')

    if request.method == 'POST':
        aksi = request.POST.get('aksi')

        if aksi not in ['Disetujui', 'Ditolak']:
            messages.error(request, 'Aksi tidak valid.')
            return redirect('kelola_klaim')

        try:
            tier_result = None
            with transaction.atomic():
                with connection.cursor() as c:
                    # Update status klaim + catat email staf
                    c.execute("""
                        UPDATE claim_missing_miles
                        SET status_penerimaan = %s, email_staf = %s
                        WHERE id = %s AND status_penerimaan = 'Menunggu'
                    """, [aksi, email_staf, id])

                    # Kalau disetujui, tambah miles ke member
                    if aksi == 'Disetujui':
                        # Hitung miles berdasarkan kelas kabin (contoh sederhana)
                        miles_map = {
                            'Economy': 500,
                            'Business': 1000,
                            'First': 2000,
                        }
                        miles = miles_map.get(klaim['kelas_kabin'], 500)

                        c.execute("""
                            UPDATE member
                            SET award_miles = COALESCE(award_miles, 0) + %s,
                                total_miles = COALESCE(total_miles, 0) + %s
                            WHERE email = %s
                        """, [miles, miles, klaim['email_member']])
                        tier_result = sync_member_tier(klaim['email_member'], cursor=c)

            messages.success(request, f'Klaim #{id} berhasil {aksi.lower()}.')
            if tier_result and tier_result['updated']:
                messages.success(
                    request,
                    f"Member naik tier dari {tier_result['previous_tier']['nama']} ke {tier_result['current_tier']['nama']}.",
                )
        except Exception as e:
            messages.error(request, f'Gagal memproses klaim: {e}')

        return redirect('kelola_klaim')

    return render(request, 'staf/klaim_proses.html', {'klaim': klaim})

"""
Tambahkan import & fungsi berikut ke dalam staf/views.py (di bawah import yang sudah ada)
"""

# ─────────────────────────────────────────────
# FITUR 6  –  CRUD MANAJEMEN DATA MEMBER (STAF)
# ─────────────────────────────────────────────

import hashlib

def hash_password(raw: str) -> str:
    """SHA-256 sederhana – sesuaikan dengan skema hash project."""
    return hashlib.sha256(raw.encode()).hexdigest()


def get_tier_list():
    with connection.cursor() as c:
        c.execute("SELECT id_tier, nama FROM tier ORDER BY minimal_tier_miles ASC")
        return [{'id_tier': r[0], 'nama': r[1]} for r in c.fetchall()]


def get_lowest_tier_id():
    with connection.cursor() as c:
        c.execute("""
            SELECT id_tier FROM tier
            ORDER BY minimal_tier_miles ASC, minimal_frekuensi_terbang ASC
            LIMIT 1
        """)
        row = c.fetchone()
    return row[0] if row else None


def generate_nomor_member():
    with connection.cursor() as c:
        c.execute("""
            SELECT nomor_member FROM member
            ORDER BY nomor_member DESC
            LIMIT 1
        """)
        row = c.fetchone()
    if row:
        last_num = int(row[0][1:])
        return f"M{last_num + 1:04d}"
    return "M0001"


# ── READ ──────────────────────────────────────

@login_required_staf
def member_list(request):
    search    = request.GET.get('search', '').strip()
    tier_filter = request.GET.get('tier', '').strip()

    query = """
        SELECT m.nomor_member,
               p.salutation || ' ' || p.first_mid_name || ' ' || p.last_name AS nama,
               m.email,
               t.nama  AS tier_nama,
               m.id_tier,
               COALESCE(m.total_miles, 0),
               COALESCE(m.award_miles, 0),
               m.tanggal_bergabung
        FROM member m
        JOIN pengguna p ON m.email = p.email
        JOIN tier t     ON m.id_tier = t.id_tier
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (p.first_mid_name ILIKE %s OR p.last_name ILIKE %s OR m.email ILIKE %s OR m.nomor_member ILIKE %s)"
        kw = f"%{search}%"
        params.extend([kw, kw, kw, kw])

    if tier_filter:
        query += " AND m.id_tier = %s"
        params.append(tier_filter)

    query += " ORDER BY m.tanggal_bergabung DESC, m.nomor_member"

    with connection.cursor() as c:
        c.execute(query, params)
        rows = c.fetchall()

    members = [{
        'nomor_member':     r[0],
        'nama':             r[1],
        'email':            r[2],
        'tier_nama':        r[3],
        'id_tier':          r[4],
        'total_miles':      r[5],
        'award_miles':      r[6],
        'tanggal_bergabung': r[7],
    } for r in rows]

    return render(request, 'staf/member_list.html', {
        'members':    members,
        'tier_list':  get_tier_list(),
        'search':     search,
        'tier_filter': tier_filter,
    })


# ── CREATE ────────────────────────────────────

@login_required_staf
def member_tambah(request):
    error = None
    tier_list = get_tier_list()

    if request.method == 'POST':
        d = request.POST
        email       = d.get('email', '').strip().lower()
        password    = d.get('password', '').strip()
        salutation  = d.get('salutation', '').strip()
        first_mid   = d.get('first_mid_name', '').strip()
        last_name   = d.get('last_name', '').strip()
        cc          = d.get('country_code', '').strip()
        mobile      = d.get('mobile_number', '').strip()
        tgl_lahir   = d.get('tanggal_lahir', '').strip()
        kewargaan   = d.get('kewarganegaraan', '').strip()

        if not all([email, password, salutation, first_mid, last_name, cc, mobile, tgl_lahir, kewargaan]):
            error = 'Semua field wajib diisi.'
        else:
            # cek duplikat email
            with connection.cursor() as c:
                c.execute("SELECT 1 FROM pengguna WHERE email = %s", [email])
                if c.fetchone():
                    error = 'Email sudah terdaftar dalam sistem.'

        if not error:
            try:
                nomor_member = generate_nomor_member()
                tier_id      = get_lowest_tier_id()
                hashed_pw    = hash_password(password)

                with transaction.atomic():
                    with connection.cursor() as c:
                        c.execute("""
                            INSERT INTO pengguna
                                (email, password, salutation, first_mid_name, last_name,
                                 country_code, mobile_number, tanggal_lahir, kewarganegaraan)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, [email, hashed_pw, salutation, first_mid, last_name,
                              cc, mobile, tgl_lahir, kewargaan])

                        c.execute("""
                            INSERT INTO member
                                (email, nomor_member, tanggal_bergabung, id_tier, award_miles, total_miles)
                            VALUES (%s, %s, CURRENT_DATE, %s, 0, 0)
                        """, [email, nomor_member, tier_id])

                messages.success(request, f'Member {nomor_member} berhasil ditambahkan.')
                return redirect('member_list_staf')
            except Exception as e:
                error = f'Gagal menambahkan member: {e}'

    return render(request, 'staf/member_form.html', {
        'mode':      'tambah',
        'error':     error,
        'tier_list': tier_list,
    })


# ── UPDATE ────────────────────────────────────

@login_required_staf
def member_edit(request, email):
    tier_list = get_tier_list()
    error     = None

    with connection.cursor() as c:
        c.execute("""
            SELECT p.salutation, p.first_mid_name, p.last_name,
                   p.country_code, p.mobile_number, p.tanggal_lahir,
                   p.kewarganegaraan,
                   m.nomor_member, m.tanggal_bergabung, m.id_tier,
                   COALESCE(m.award_miles,0), COALESCE(m.total_miles,0)
            FROM pengguna p
            JOIN member m ON m.email = p.email
            WHERE p.email = %s
        """, [email])
        row = c.fetchone()

    if not row:
        messages.error(request, 'Member tidak ditemukan.')
        return redirect('member_list_staf')

    member = {
        'email':            email,
        'salutation':       row[0],
        'first_mid_name':   row[1],
        'last_name':        row[2],
        'country_code':     row[3],
        'mobile_number':    row[4],
        'tanggal_lahir':    row[5].strftime('%Y-%m-%d') if row[5] else '',
        'kewarganegaraan':  row[6],
        'nomor_member':     row[7],
        'tanggal_bergabung': row[8],
        'id_tier':          row[9],
        'award_miles':      row[10],
        'total_miles':      row[11],
    }

    if request.method == 'POST':
        d = request.POST
        salutation  = d.get('salutation', '').strip()
        first_mid   = d.get('first_mid_name', '').strip()
        last_name   = d.get('last_name', '').strip()
        cc          = d.get('country_code', '').strip()
        mobile      = d.get('mobile_number', '').strip()
        tgl_lahir   = d.get('tanggal_lahir', '').strip()
        kewargaan   = d.get('kewarganegaraan', '').strip()
        id_tier     = d.get('id_tier', '').strip()

        if not all([salutation, first_mid, last_name, cc, mobile, tgl_lahir, kewargaan, id_tier]):
            error = 'Semua field wajib diisi.'
        else:
            try:
                with transaction.atomic():
                    with connection.cursor() as c:
                        c.execute("""
                            UPDATE pengguna SET
                                salutation=%s, first_mid_name=%s, last_name=%s,
                                country_code=%s, mobile_number=%s,
                                tanggal_lahir=%s, kewarganegaraan=%s
                            WHERE email=%s
                        """, [salutation, first_mid, last_name, cc, mobile,
                              tgl_lahir, kewargaan, email])

                        c.execute("""
                            UPDATE member SET id_tier=%s WHERE email=%s
                        """, [id_tier, email])

                messages.success(request, 'Data member berhasil diperbarui.')
                return redirect('member_list_staf')
            except Exception as e:
                error = f'Gagal memperbarui data: {e}'

        member.update({
            'salutation': salutation, 'first_mid_name': first_mid,
            'last_name': last_name, 'country_code': cc,
            'mobile_number': mobile, 'tanggal_lahir': tgl_lahir,
            'kewarganegaraan': kewargaan, 'id_tier': id_tier,
        })

    return render(request, 'staf/member_form.html', {
        'mode':      'edit',
        'member':    member,
        'tier_list': tier_list,
        'error':     error,
    })


# ── DELETE ────────────────────────────────────

@login_required_staf
def member_hapus(request, email):
    with connection.cursor() as c:
        c.execute("""
            SELECT p.salutation || ' ' || p.first_mid_name || ' ' || p.last_name,
                   m.nomor_member
            FROM pengguna p
            JOIN member m ON m.email = p.email
            WHERE p.email = %s
        """, [email])
        row = c.fetchone()

    if not row:
        messages.error(request, 'Member tidak ditemukan.')
        return redirect('member_list_staf')

    nama, nomor_member = row

    if request.method == 'POST':
        try:
            with transaction.atomic():
                with connection.cursor() as c:
                    # ON DELETE CASCADE sudah handle relasi child
                    c.execute("DELETE FROM member  WHERE email = %s", [email])
                    c.execute("DELETE FROM pengguna WHERE email = %s", [email])
            messages.success(request, f'Member {nomor_member} ({nama}) berhasil dihapus.')
        except Exception as e:
            messages.error(request, f'Gagal menghapus member: {e}')
        return redirect('member_list_staf')

    return render(request, 'staf/member_hapus.html', {
        'email':        email,
        'nama':         nama,
        'nomor_member': nomor_member,
    })