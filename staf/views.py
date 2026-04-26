from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection


def login_required_staf(view_func):
    """Decorator cek login dan role staf."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_email'):
            return redirect('login')
        if request.session.get('role') != 'staf':
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# FITUR 9

@login_required_staf
def klaim_list_staf(request):
    email_staf = request.session['user_email']

    # Filter params
    status_filter   = request.GET.get('status', '')
    maskapai_filter = request.GET.get('maskapai', '')
    tgl_dari        = request.GET.get('tgl_dari', '')
    tgl_sampai      = request.GET.get('tgl_sampai', '')

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

    klaim_list = []
    for r in rows:
        klaim_list.append({
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
        })

    # Ambil daftar maskapai untuk filter dropdown
    with connection.cursor() as c:
        c.execute("SELECT kode_maskapai, nama_maskapai FROM maskapai ORDER BY nama_maskapai")
        maskapai_list = [{'kode': r[0], 'nama': r[1]} for r in c.fetchall()]

    return render(request, 'staf/klaim_list_staf.html', {
        'klaim_list':      klaim_list,
        'maskapai_list':   maskapai_list,
        'status_filter':   status_filter,
        'maskapai_filter': maskapai_filter,
        'tgl_dari':        tgl_dari,
        'tgl_sampai':      tgl_sampai,
    })


@login_required_staf
def klaim_proses(request, id):
    email_staf = request.session['user_email']

    # Ambil data klaim
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
        aksi = request.POST.get('aksi')  # 'Disetujui' atau 'Ditolak'

        if aksi not in ['Disetujui', 'Ditolak']:
            messages.error(request, 'Aksi tidak valid.')
            return redirect('kelola_klaim')

        try:
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

                with connection.cursor() as c:
                    c.execute("""
                        UPDATE member
                        SET award_miles = COALESCE(award_miles, 0) + %s,
                            total_miles = COALESCE(total_miles, 0) + %s
                        WHERE email = %s
                    """, [miles, miles, klaim['email_member']])

            messages.success(request, f'Klaim #{id} berhasil {aksi.lower()}.')
        except Exception as e:
            messages.error(request, f'Gagal memproses klaim: {e}')

        return redirect('kelola_klaim')

    return render(request, 'staf/klaim_proses.html', {'klaim': klaim})
