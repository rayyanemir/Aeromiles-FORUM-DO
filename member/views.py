from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from datetime import date
from datetime import date as _date
 
 
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
 
 
def get_member_miles(email):
    with connection.cursor() as c:
        c.execute("""
            SELECT nomor_member, COALESCE(award_miles, 0), COALESCE(total_miles, 0)
            FROM member
            WHERE email = %s
        """, [email])
        row = c.fetchone()
 
    if not row:
        return None
 
    return {
        'nomor_member': row[0],
        'award_miles':  row[1],
        'total_miles':  row[2],
    }
 
 
def get_redeem_catalog(email):
    today = date.today()
 
    with connection.cursor() as c:
        c.execute("""
            SELECT h.kode_hadiah,
                   h.nama,
                   h.miles,
                   h.deskripsi,
                   h.valid_start_date,
                   h.program_end,
                   COALESCE(mt.nama_mitra, mk.nama_maskapai, 'Penyedia #' || h.id_penyedia::text) AS penyedia,
                   EXISTS (
                       SELECT 1 FROM redeem r
                       WHERE r.email_member = %s AND r.kode_hadiah = h.kode_hadiah
                   ) AS pernah_redeem
            FROM hadiah h
            LEFT JOIN mitra mt ON h.id_penyedia = mt.id_penyedia
            LEFT JOIN maskapai mk ON h.id_penyedia = mk.id_penyedia
            ORDER BY h.program_end ASC, h.miles ASC, h.nama ASC
        """, [email])
        rows = c.fetchall()
 
    hadiah_list = []
    for row in rows:
        hadiah = {
            'kode_hadiah':   row[0],
            'nama':          row[1],
            'miles':         row[2],
            'deskripsi':     row[3],
            'valid_start_date': row[4],
            'program_end':   row[5],
            'penyedia':      row[6],
            'pernah_redeem': row[7],
        }
 
        if today < hadiah['valid_start_date']:
            hadiah['status'] = 'akan_datang'
            hadiah['status_label'] = 'Akan Datang'
        elif today > hadiah['program_end']:
            hadiah['status'] = 'berakhir'
            hadiah['status_label'] = 'Berakhir'
        else:
            hadiah['status'] = 'tersedia'
            hadiah['status_label'] = 'Tersedia'
 
        hadiah_list.append(hadiah)
 
    return hadiah_list
 
 
def get_redeem_history(email):
    with connection.cursor() as c:
        c.execute("""
            SELECT r.timestamp,
                   h.kode_hadiah,
                   h.nama,
                   h.miles,
                   COALESCE(mt.nama_mitra, mk.nama_maskapai, 'Penyedia #' || h.id_penyedia::text) AS penyedia
            FROM redeem r
            JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah
            LEFT JOIN mitra mt ON h.id_penyedia = mt.id_penyedia
            LEFT JOIN maskapai mk ON h.id_penyedia = mk.id_penyedia
            WHERE r.email_member = %s
            ORDER BY r.timestamp DESC
        """, [email])
        rows = c.fetchall()
 
    return [{
        'timestamp':   row[0],
        'kode_hadiah': row[1],
        'nama':        row[2],
        'miles':       row[3],
        'penyedia':    row[4],
    } for row in rows]
 
 
def get_package_catalog():
    with connection.cursor() as c:
        c.execute("""
            SELECT id, jumlah_award_miles, harga_paket
            FROM award_miles_package
            ORDER BY jumlah_award_miles ASC, harga_paket ASC
        """)
        rows = c.fetchall()
 
    return [{
        'id':                row[0],
        'jumlah_award_miles': row[1],
        'harga_paket':       row[2],
    } for row in rows]
 
 
def get_package_history(email):
    with connection.cursor() as c:
        c.execute("""
            SELECT mp.timestamp, amp.id, amp.jumlah_award_miles, amp.harga_paket
            FROM member_award_miles_package mp
            JOIN award_miles_package amp ON mp.id_award_miles_package = amp.id
            WHERE mp.email_member = %s
            ORDER BY mp.timestamp DESC
        """, [email])
        rows = c.fetchall()
 
    return [{
        'timestamp':          row[0],
        'id':                 row[1],
        'jumlah_award_miles': row[2],
        'harga_paket':        row[3],
    } for row in rows]
 
 
def get_tier_information(email):
    benefits_map = {
        'Blue': ['Akumulasi miles dasar', 'Akses penawaran khusus member'],
        'Silver': ['Bonus miles 25%', 'Priority check-in', 'Akses lounge partner'],
        'Gold': ['Bonus miles 50%', 'Priority boarding', 'Akses lounge premium', 'Extra bagasi 10kg'],
        'Platinum': ['Bonus miles 100%', 'Upgrade gratis (subject to availability)', 'Akses lounge first class', 'Extra bagasi 20kg', 'Dedicated hotline'],
    }
 
    with connection.cursor() as c:
        c.execute("""
            SELECT m.id_tier, COALESCE(m.total_miles, 0), COALESCE(m.award_miles, 0), t.nama
            FROM member m
            JOIN tier t ON m.id_tier = t.id_tier
            WHERE m.email = %s
        """, [email])
        member_row = c.fetchone()
 
    if not member_row:
        return None
 
    current_tier_id   = member_row[0]
    total_miles       = member_row[1]
    award_miles       = member_row[2]
    current_tier_name = member_row[3]
 
    with connection.cursor() as c:
        c.execute("""
            SELECT id_tier, nama, minimal_frekuensi_terbang, minimal_tier_miles
            FROM tier
            ORDER BY minimal_tier_miles ASC, minimal_frekuensi_terbang ASC
        """)
        rows = c.fetchall()
 
    tiers = [{
        'id_tier':                   row[0],
        'nama':                      row[1],
        'minimal_frekuensi_terbang': row[2],
        'minimal_tier_miles':        row[3],
        'benefits':                  benefits_map.get(row[1], []),
        'is_current':                row[0] == current_tier_id,
    } for row in rows]
 
    current_index = next((i for i, t in enumerate(tiers) if t['id_tier'] == current_tier_id), 0)
    current_tier  = tiers[current_index]
    next_tier     = tiers[current_index + 1] if current_index + 1 < len(tiers) else None
    previous_threshold = tiers[current_index - 1]['minimal_tier_miles'] if current_index > 0 else 0
 
    progress = {
        'current_tier_name': current_tier_name,
        'total_miles':       total_miles,
        'award_miles':       award_miles,
        'next_tier':         next_tier,
        'miles_to_next_tier': 0,
        'percent':           100,
        'range_start':       previous_threshold,
        'range_end':         current_tier['minimal_tier_miles'],
    }
 
    if next_tier:
        range_start  = current_tier['minimal_tier_miles']
        range_end    = next_tier['minimal_tier_miles']
        range_size   = max(range_end - range_start, 1)
        current_prog = min(max(total_miles - range_start, 0), range_size)
        progress.update({
            'next_tier':          next_tier,
            'miles_to_next_tier': max(next_tier['minimal_tier_miles'] - total_miles, 0),
            'percent':            round((current_prog / range_size) * 100, 2),
            'range_start':        range_start,
            'range_end':          range_end,
        })
 
    return {'tiers': tiers, 'progress': progress}
 
 
def get_identitas_list(email_member):
    today = _date.today()
    with connection.cursor() as c:
        c.execute("""
            SELECT nomor, jenis, negara_penerbit, tanggal_terbit, tanggal_habis
            FROM identitas
            WHERE email_member = %s
            ORDER BY tanggal_habis ASC
        """, [email_member])
        rows = c.fetchall()
 
    result = []
    for r in rows:
        tgl_habis = r[4]
        if tgl_habis < today:
            status = 'kadaluarsa'
        elif (tgl_habis - today).days <= 90:
            status = 'segera_habis'
        else:
            status = 'aktif'
 
        result.append({
            'nomor':           r[0],
            'jenis':           r[1],
            'negara_penerbit': r[2],
            'tanggal_terbit':  r[3],
            'tanggal_habis':   tgl_habis,
            'status':          status,
        })
    return result
 
 
@login_required_member
def klaim_list(request):
    email         = request.session['user_email']
    status_filter = request.GET.get('status', '')
    is_ajax       = request.GET.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    klaim_data    = get_klaim_list(email, status_filter)
    context       = {'klaim_list': klaim_data, 'status_filter': status_filter}
 
    if is_ajax:
        return render(request, 'member/klaim_table_partial.html', context)
    return render(request, 'member/klaim_list.html', context)
 
 
@login_required_member
def klaim_buat(request):
    email = request.session['user_email']
    maskapai_list, bandara_list = get_dropdown_data()
    error = None
 
    if request.method == 'POST':
        d               = request.POST
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
                err_msg = str(e)
                if 'ERROR:' in err_msg:
                    err_msg = err_msg.split('ERROR:')[-1].strip()
                error = err_msg
 
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
        d               = request.POST
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
 
 
@login_required_member
def redeem_list(request):
    email       = request.session['user_email']
    member_info = get_member_miles(email)
 
    if not member_info:
        messages.error(request, 'Data member tidak ditemukan.')
        return redirect('dashboard')
 
    hadiah_list = [item for item in get_redeem_catalog(email) if item['status'] != 'berakhir']
    riwayat_redeem = get_redeem_history(email)
 
    for hadiah in hadiah_list:
        hadiah['selisih_miles'] = hadiah['miles'] - member_info['award_miles']
 
    status_filter = request.GET.get('status', '').strip().lower()
    valid_statuses = {'tersedia', 'akan_datang'}
    if status_filter in valid_statuses:
        hadiah_list = [item for item in hadiah_list if item['status'] == status_filter]
    else:
        status_filter = ''
 
    return render(request, 'member/redeem_list.html', {
        'member_info':   member_info,
        'hadiah_list':   hadiah_list,
        'riwayat_redeem': riwayat_redeem,
        'status_filter': status_filter,
        'today':         date.today(),
    })
 
 
@login_required_member
def redeem_buat(request, kode_hadiah):
    email       = request.session['user_email']
    member_info = get_member_miles(email)
 
    if not member_info:
        messages.error(request, 'Data member tidak ditemukan.')
        return redirect('dashboard')
 
    hadiah = next(
        (item for item in get_redeem_catalog(email) if item['kode_hadiah'] == kode_hadiah),
        None,
    )
 
    if not hadiah:
        messages.error(request, 'Hadiah tidak ditemukan.')
        return redirect('redeem_list')
 
    hadiah['sisa_setelah_redeem'] = member_info['award_miles'] - hadiah['miles']
 
    if request.method == 'POST':
        try:
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO redeem (email_member, kode_hadiah, timestamp)
                    VALUES (%s, %s, NOW())
                """, [email, kode_hadiah])
            messages.success(request, f"Redeem hadiah '{hadiah['nama']}' berhasil diproses.")
            return redirect('redeem_list')
        except Exception as e:
            err_msg = str(e)
            if 'ERROR:' in err_msg:
                err_msg = err_msg.split('ERROR:')[-1].strip()
            messages.error(request, err_msg)
 
    return render(request, 'member/redeem_form.html', {
        'member_info': member_info,
        'hadiah':      hadiah,
        'today':       date.today(),
    })
 
 
@login_required_member
def package_list(request):
    email       = request.session['user_email']
    member_info = get_member_miles(email)
 
    if not member_info:
        messages.error(request, 'Data member tidak ditemukan.')
        return redirect('dashboard')
 
    return render(request, 'member/package_list.html', {
        'member_info':     member_info,
        'package_list':    get_package_catalog(),
        'riwayat_package': get_package_history(email),
    })
 
 
@login_required_member
def package_beli(request, package_id):
    email       = request.session['user_email']
    member_info = get_member_miles(email)
 
    if not member_info:
        messages.error(request, 'Data member tidak ditemukan.')
        return redirect('dashboard')
 
    selected_package = next(
        (item for item in get_package_catalog() if item['id'] == package_id),
        None,
    )
 
    if not selected_package:
        messages.error(request, 'Package tidak ditemukan.')
        return redirect('package_list')
 
    selected_package['saldo_setelah_beli'] = member_info['award_miles'] + selected_package['jumlah_award_miles']
 
    if request.method == 'POST':
        try:
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO member_award_miles_package
                        (id_award_miles_package, email_member, timestamp)
                    VALUES (%s, %s, NOW())
                """, [package_id, email])
            messages.success(
                request,
                f"Pembelian package '{selected_package['id']}' berhasil. Award miles bertambah {selected_package['jumlah_award_miles']}.",
            )
            return redirect('package_list')
        except Exception as e:
            err_msg = str(e)
            if 'ERROR:' in err_msg:
                err_msg = err_msg.split('ERROR:')[-1].strip()
            messages.error(request, err_msg)
 
    return render(request, 'member/package_form.html', {
        'member_info': member_info,
        'package':     selected_package,
    })
 
 
@login_required_member
def tier_info(request):
    email          = request.session['user_email']
    tier_info_data = get_tier_information(email)
 
    if not tier_info_data:
        messages.error(request, 'Data member tidak ditemukan.')
        return redirect('dashboard')
 
    return render(request, 'member/tier_info.html', tier_info_data)
 
 
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
 
        cols          = ['tipe', 'timestamp', 'jumlah', 'catatan', 'nama_lawan', 'email_lawan']
        transfer_data = [dict(zip(cols, r)) for r in c.fetchall()]
 
    return render(request, 'member/transfer_list.html', {'transfer_list': transfer_data})
 
 
@login_required_member
def transfer_buat(request):
    email = request.session['user_email']
    error = None
 
    with connection.cursor() as c:
        c.execute("SELECT award_miles FROM member WHERE email = %s", [email])
        row         = c.fetchone()
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
                else:
                    with connection.cursor() as c:
                        c.execute("SELECT email FROM member WHERE email = %s", [email_penerima])
                        penerima = c.fetchone()
 
                    if not penerima:
                        error = 'Email penerima tidak terdaftar sebagai member.'
                    else:
                        try:
                            with connection.cursor() as c:
                                c.execute("""
                                    INSERT INTO transfer
                                        (email_member_1, email_member_2, timestamp, jumlah, catatan)
                                    VALUES (%s, %s, NOW(), %s, %s)
                                """, [email, email_penerima, jumlah, catatan or None])
                            messages.success(request, f'Transfer {jumlah} miles berhasil!')
                            return redirect('transfer_list')
                        except Exception as e:
                            err_msg = str(e)
                            if 'ERROR:' in err_msg:
                                err_msg = err_msg.split('ERROR:')[-1].strip()
                            error = err_msg
            except ValueError:
                error = 'Jumlah miles harus berupa angka.'
 
    return render(request, 'member/transfer_form.html', {
        'award_miles': award_miles,
        'error':       error,
    })
 
 
@login_required_member
def identitas_list(request):
    email = request.session['user_email']
    return render(request, 'member/identitas_list.html', {
        'identitas_list': get_identitas_list(email),
        'today':          _date.today(),
    })
 
 
@login_required_member
def identitas_tambah(request):
    email = request.session['user_email']
    error = None
 
    if request.method == 'POST':
        d          = request.POST
        nomor      = d.get('nomor', '').strip()
        jenis      = d.get('jenis', '').strip()
        negara     = d.get('negara_penerbit', '').strip()
        tgl_terbit = d.get('tanggal_terbit', '').strip()
        tgl_habis  = d.get('tanggal_habis', '').strip()
 
        if not all([nomor, jenis, negara, tgl_terbit, tgl_habis]):
            error = 'Semua field wajib diisi.'
        elif jenis not in ('Paspor', 'KTP', 'SIM'):
            error = 'Jenis identitas tidak valid.'
        elif tgl_terbit >= tgl_habis:
            error = 'Tanggal habis harus setelah tanggal terbit.'
        else:
            with connection.cursor() as c:
                c.execute("SELECT 1 FROM identitas WHERE nomor = %s", [nomor])
                if c.fetchone():
                    error = 'Nomor dokumen sudah terdaftar dalam sistem.'
 
        if not error:
            try:
                with connection.cursor() as c:
                    c.execute("""
                        INSERT INTO identitas
                            (nomor, email_member, jenis, negara_penerbit, tanggal_terbit, tanggal_habis)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, [nomor, email, jenis, negara, tgl_terbit, tgl_habis])
                messages.success(request, f'Identitas {jenis} ({nomor}) berhasil ditambahkan.')
                return redirect('identitas_list')
            except Exception as e:
                error = f'Gagal menyimpan identitas: {e}'
 
    return render(request, 'member/identitas_form.html', {'mode': 'tambah', 'error': error})
 
 
@login_required_member
def identitas_edit(request, nomor):
    email = request.session['user_email']
    error = None
 
    with connection.cursor() as c:
        c.execute("""
            SELECT nomor, jenis, negara_penerbit, tanggal_terbit, tanggal_habis
            FROM identitas
            WHERE nomor = %s AND email_member = %s
        """, [nomor, email])
        row = c.fetchone()
 
    if not row:
        messages.error(request, 'Dokumen identitas tidak ditemukan.')
        return redirect('identitas_list')
 
    identitas = {
        'nomor':           row[0],
        'jenis':           row[1],
        'negara_penerbit': row[2],
        'tanggal_terbit':  row[3].strftime('%Y-%m-%d') if row[3] else '',
        'tanggal_habis':   row[4].strftime('%Y-%m-%d') if row[4] else '',
    }
 
    if request.method == 'POST':
        d          = request.POST
        jenis      = d.get('jenis', '').strip()
        negara     = d.get('negara_penerbit', '').strip()
        tgl_terbit = d.get('tanggal_terbit', '').strip()
        tgl_habis  = d.get('tanggal_habis', '').strip()
 
        if not all([jenis, negara, tgl_terbit, tgl_habis]):
            error = 'Semua field wajib diisi.'
        elif jenis not in ('Paspor', 'KTP', 'SIM'):
            error = 'Jenis identitas tidak valid.'
        elif tgl_terbit >= tgl_habis:
            error = 'Tanggal habis harus setelah tanggal terbit.'
        else:
            try:
                with connection.cursor() as c:
                    c.execute("""
                        UPDATE identitas SET
                            jenis=%s, negara_penerbit=%s, tanggal_terbit=%s, tanggal_habis=%s
                        WHERE nomor=%s AND email_member=%s
                    """, [jenis, negara, tgl_terbit, tgl_habis, nomor, email])
                messages.success(request, 'Identitas berhasil diperbarui.')
                return redirect('identitas_list')
            except Exception as e:
                error = f'Gagal memperbarui identitas: {e}'
 
        identitas.update({
            'jenis': jenis, 'negara_penerbit': negara,
            'tanggal_terbit': tgl_terbit, 'tanggal_habis': tgl_habis,
        })
 
    return render(request, 'member/identitas_form.html', {
        'mode':      'edit',
        'identitas': identitas,
        'error':     error,
    })
 
 
@login_required_member
def identitas_hapus(request, nomor):
    email = request.session['user_email']
 
    with connection.cursor() as c:
        c.execute("""
            SELECT nomor, jenis, negara_penerbit
            FROM identitas
            WHERE nomor=%s AND email_member=%s
        """, [nomor, email])
        row = c.fetchone()
 
    if not row:
        messages.error(request, 'Dokumen identitas tidak ditemukan.')
        return redirect('identitas_list')
 
    identitas = {'nomor': row[0], 'jenis': row[1], 'negara_penerbit': row[2]}
 
    if request.method == 'POST':
        with connection.cursor() as c:
            c.execute("DELETE FROM identitas WHERE nomor=%s AND email_member=%s", [nomor, email])
        messages.success(request, f'Identitas {identitas["jenis"]} ({nomor}) berhasil dihapus.')
        return redirect('identitas_list')
 
    return render(request, 'member/identitas_hapus.html', {'identitas': identitas})