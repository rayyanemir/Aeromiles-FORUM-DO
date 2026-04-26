from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from datetime import datetime


def login_required_member(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_email'):
            return redirect('login')
        if request.session.get('role') != 'member':
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_dropdown_data():
    with connection.cursor() as c:
        c.execute("SELECT kode_maskapai, nama_maskapai FROM maskapai ORDER BY nama_maskapai")
        maskapai_list = [{'kode': r[0], 'nama': r[1]} for r in c.fetchall()]

    with connection.cursor() as c:
        c.execute("SELECT iata_code, nama, kota, negara FROM bandara ORDER BY kota")
        bandara_list = [{'iata': r[0], 'nama': r[1], 'kota': r[2], 'negara': r[3]} for r in c.fetchall()]

    return maskapai_list, bandara_list


def get_klaim_list(email, status_filter=''):
    query = """
        SELECT cm.id, mk.nama_maskapai, ba.iata_code, ba.nama, bt.iata_code, bt.nama,
               cm.tanggal_penerbangan, cm.flight_number, cm.kelas_kabin,
               cm.status_penerimaan, cm.timestamp, cm.nomor_tiket, cm.pnr
        FROM claim_missing_miles cm
        JOIN maskapai mk ON cm.maskapai = mk.kode_maskapai
        JOIN bandara ba ON cm.bandara_asal = ba.iata_code
        JOIN bandara bt ON cm.bandara_tujuan = bt.iata_code
        WHERE cm.email_member = %s
    """
    params = [email]

    if status_filter:
        query += " AND cm.status_penerimaan = %s"
        params.append(status_filter)

    query += " ORDER BY cm.timestamp DESC"

    with connection.cursor() as c:
        c.execute(query, params)
        rows = c.fetchall()

    return [{
        'id':                  r[0],
        'maskapai':            r[1],
        'bandara_asal_code':   r[2],
        'bandara_asal_nama':   r[3],
        'bandara_tujuan_code': r[4],
        'bandara_tujuan_nama': r[5],
        'tanggal_penerbangan': r[6],
        'flight_number':       r[7],
        'kelas_kabin':         r[8],
        'status':              r[9],
        'timestamp':           r[10],
        'nomor_tiket':         r[11],
        'pnr':                 r[12],
    } for r in rows]


# FITUR 8

@login_required_member
def klaim_list(request):
    email = request.session['user_email']
    status_filter = request.GET.get('status', '')
    is_ajax = request.GET.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    klaim_data = get_klaim_list(email, status_filter)

    context = {
        'klaim_list':    klaim_data,
        'status_filter': status_filter,
    }

    if is_ajax:
        return render(request, 'member/klaim_table_partial.html', context)

    return render(request, 'member/klaim_list.html', context)


@login_required_member
def klaim_buat(request):
    email = request.session['user_email']
    maskapai_list, bandara_list = get_dropdown_data()
    error = None

    if request.method == 'POST':
        d = request.POST
        maskapai        = d.get('maskapai')
        bandara_asal    = d.get('bandara_asal')
        bandara_tujuan  = d.get('bandara_tujuan')
        tgl_penerbangan = d.get('tanggal_penerbangan')
        flight_number   = d.get('flight_number', '').strip()
        nomor_tiket     = d.get('nomor_tiket', '').strip()
        kelas_kabin     = d.get('kelas_kabin')
        pnr             = d.get('pnr', '').strip()

        if not all([maskapai, bandara_asal, bandara_tujuan, tgl_penerbangan,
                    flight_number, nomor_tiket, kelas_kabin, pnr]):
            error = 'Semua field wajib diisi.'
        elif bandara_asal == bandara_tujuan:
            error = 'Bandara asal dan tujuan tidak boleh sama.'
        else:
            with connection.cursor() as c:
                c.execute("""
                    SELECT id FROM claim_missing_miles
                    WHERE email_member = %s AND flight_number = %s
                      AND tanggal_penerbangan = %s AND nomor_tiket = %s
                """, [email, flight_number, tgl_penerbangan, nomor_tiket])
                if c.fetchone():
                    error = 'Klaim untuk penerbangan ini sudah pernah diajukan.'

        if not error:
            try:
                with connection.cursor() as c:
                    c.execute("""
                        INSERT INTO claim_missing_miles
                            (email_member, maskapai, bandara_asal, bandara_tujuan,
                             tanggal_penerbangan, flight_number, nomor_tiket,
                             kelas_kabin, pnr, status_penerimaan, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Menunggu', NOW())
                    """, [email, maskapai, bandara_asal, bandara_tujuan,
                          tgl_penerbangan, flight_number, nomor_tiket, kelas_kabin, pnr])
                messages.success(request, 'Klaim berhasil diajukan!')
                return redirect('klaim_list')
            except Exception as e:
                error = f'Gagal mengajukan klaim: {e}'

    return render(request, 'member/klaim_form.html', {
        'maskapai_list': maskapai_list,
        'bandara_list':  bandara_list,
        'error':         error,
        'mode':          'buat',
    })


@login_required_member
def klaim_edit(request, id):
    email = request.session['user_email']
    maskapai_list, bandara_list = get_dropdown_data()
    error = None

    with connection.cursor() as c:
        c.execute("""
            SELECT id, maskapai, bandara_asal, bandara_tujuan,
                   tanggal_penerbangan, flight_number, nomor_tiket,
                   kelas_kabin, pnr, status_penerimaan
            FROM claim_missing_miles
            WHERE id = %s AND email_member = %s
        """, [id, email])
        row = c.fetchone()

    if not row:
        messages.error(request, 'Klaim tidak ditemukan.')
        return redirect('klaim_list')

    klaim = {
        'id':                  row[0],
        'maskapai':            row[1],
        'bandara_asal':        row[2],
        'bandara_tujuan':      row[3],
        'tanggal_penerbangan': row[4].strftime('%Y-%m-%d') if row[4] else '',
        'flight_number':       row[5],
        'nomor_tiket':         row[6],
        'kelas_kabin':         row[7],
        'pnr':                 row[8],
        'status':              row[9],
    }

    if klaim['status'] != 'Menunggu':
        messages.error(request, 'Klaim yang sudah diproses tidak dapat diubah.')
        return redirect('klaim_list')

    if request.method == 'POST':
        d = request.POST
        maskapai        = d.get('maskapai')
        bandara_asal    = d.get('bandara_asal')
        bandara_tujuan  = d.get('bandara_tujuan')
        tgl_penerbangan = d.get('tanggal_penerbangan')
        flight_number   = d.get('flight_number', '').strip()
        nomor_tiket     = d.get('nomor_tiket', '').strip()
        kelas_kabin     = d.get('kelas_kabin')
        pnr             = d.get('pnr', '').strip()

        if not all([maskapai, bandara_asal, bandara_tujuan, tgl_penerbangan,
                    flight_number, nomor_tiket, kelas_kabin, pnr]):
            error = 'Semua field wajib diisi.'
        elif bandara_asal == bandara_tujuan:
            error = 'Bandara asal dan tujuan tidak boleh sama.'

        if not error:
            try:
                with connection.cursor() as c:
                    c.execute("""
                        UPDATE claim_missing_miles SET
                            maskapai = %s, bandara_asal = %s, bandara_tujuan = %s,
                            tanggal_penerbangan = %s, flight_number = %s,
                            nomor_tiket = %s, kelas_kabin = %s, pnr = %s
                        WHERE id = %s AND email_member = %s AND status_penerimaan = 'Menunggu'
                    """, [maskapai, bandara_asal, bandara_tujuan, tgl_penerbangan,
                          flight_number, nomor_tiket, kelas_kabin, pnr, id, email])
                messages.success(request, 'Klaim berhasil diperbarui!')
                return redirect('klaim_list')
            except Exception as e:
                error = f'Gagal memperbarui klaim: {e}'

 
        klaim.update({
            'maskapai': maskapai, 'bandara_asal': bandara_asal,
            'bandara_tujuan': bandara_tujuan, 'tanggal_penerbangan': tgl_penerbangan,
            'flight_number': flight_number, 'nomor_tiket': nomor_tiket,
            'kelas_kabin': kelas_kabin, 'pnr': pnr,
        })

    return render(request, 'member/klaim_form.html', {
        'maskapai_list': maskapai_list,
        'bandara_list':  bandara_list,
        'klaim':         klaim,
        'error':         error,
        'mode':          'edit',
    })


@login_required_member
def klaim_hapus(request, id):
    email = request.session['user_email']

    with connection.cursor() as c:
        c.execute("""
            SELECT status_penerimaan FROM claim_missing_miles
            WHERE id = %s AND email_member = %s
        """, [id, email])
        row = c.fetchone()

    if not row:
        messages.error(request, 'Klaim tidak ditemukan.')
        return redirect('klaim_list')

    if row[0] != 'Menunggu':
        messages.error(request, 'Hanya klaim berstatus Menunggu yang dapat dibatalkan.')
        return redirect('klaim_list')

    if request.method == 'POST':
        with connection.cursor() as c:
            c.execute("""
                DELETE FROM claim_missing_miles
                WHERE id = %s AND email_member = %s AND status_penerimaan = 'Menunggu'
            """, [id, email])
        messages.success(request, 'Klaim berhasil dibatalkan.')
        return redirect('klaim_list')

    with connection.cursor() as c:
        c.execute("""
            SELECT cm.flight_number, mk.nama_maskapai, cm.tanggal_penerbangan
            FROM claim_missing_miles cm
            JOIN maskapai mk ON cm.maskapai = mk.kode_maskapai
            WHERE cm.id = %s
        """, [id])
        detail = c.fetchone()

    return render(request, 'member/klaim_hapus.html', {
        'id':            id,
        'flight_number': detail[0],
        'maskapai':      detail[1],
        'tanggal':       detail[2],
    })


#  FITUR 10

@login_required_member
def transfer_list(request):
    email = request.session['user_email']

    with connection.cursor() as c:
        c.execute("""
            SELECT 'Kirim' AS tipe,
                   t.timestamp, t.jumlah, t.catatan,
                   p.first_mid_name || ' ' || p.last_name AS nama_lawan,
                   m2.email AS email_lawan
            FROM transfer t
            JOIN member m2 ON t.email_member_2 = m2.email
            JOIN pengguna p ON m2.email = p.email
            WHERE t.email_member_1 = %s

            UNION ALL

            SELECT 'Terima',
                   t.timestamp, t.jumlah, t.catatan,
                   p.first_mid_name || ' ' || p.last_name,
                   m1.email
            FROM transfer t
            JOIN member m1 ON t.email_member_1 = m1.email
            JOIN pengguna p ON m1.email = p.email
            WHERE t.email_member_2 = %s

            ORDER BY timestamp DESC
        """, [email, email])

        cols = ['tipe', 'timestamp', 'jumlah', 'catatan', 'nama_lawan', 'email_lawan']
        transfer_data = [dict(zip(cols, r)) for r in c.fetchall()]

    return render(request, 'member/transfer_list.html', {
        'transfer_list': transfer_data,
    })


@login_required_member
def transfer_buat(request):
    email = request.session['user_email']
    error = None

    with connection.cursor() as c:
        c.execute("SELECT award_miles FROM member WHERE email = %s", [email])
        row = c.fetchone()
        award_miles = row[0] or 0

    if request.method == 'POST':
        email_penerima = request.POST.get('email_penerima', '').strip()
        jumlah         = request.POST.get('jumlah', '').strip()
        catatan        = request.POST.get('catatan', '').strip()

        if not email_penerima or not jumlah:
            error = 'Email penerima dan jumlah wajib diisi.'
        elif email_penerima == email:
            error = 'Tidak dapat mentransfer miles ke diri sendiri.'
        else:
            try:
                jumlah = int(jumlah)
                if jumlah <= 0:
                    error = 'Jumlah miles harus lebih dari 0.'
                elif jumlah > award_miles:
                    error = f'Award miles tidak mencukupi. Saldo kamu: {award_miles} miles.'
                else:
                    with connection.cursor() as c:
                        c.execute("SELECT email FROM member WHERE email = %s", [email_penerima])
                        penerima = c.fetchone()

                    if not penerima:
                        error = 'Email penerima tidak terdaftar sebagai member.'
                    else:
                        with connection.cursor() as c:
                            c.execute("""
                                INSERT INTO transfer
                                    (email_member_1, email_member_2, timestamp, jumlah, catatan)
                                VALUES (%s, %s, NOW(), %s, %s)
                            """, [email, email_penerima, jumlah, catatan or None])
                        messages.success(request, f'Transfer {jumlah} miles berhasil!')
                        return redirect('transfer_list')
            except ValueError:
                error = 'Jumlah miles harus berupa angka.'
            except Exception as e:
                error = f'Gagal transfer: {e}'

    return render(request, 'member/transfer_form.html', {
        'award_miles': award_miles,
        'error':       error,
    })
