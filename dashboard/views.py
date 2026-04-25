from django.shortcuts import render, redirect
from django.db import connection


def dashboard_view(request):
    # Cek login
    email = request.session.get('user_email')
    role  = request.session.get('role')
    if not email:
        return redirect('login')

    # Data umum semua role
    with connection.cursor() as c:
        c.execute("""
            SELECT email, salutation, first_mid_name, last_name,
                   country_code, mobile_number, tanggal_lahir, kewarganegaraan
            FROM pengguna WHERE email = %s
        """, [email])
        row = c.fetchone()

    pengguna = {
        'email':           row[0],
        'salutation':      row[1],
        'first_mid_name':  row[2],
        'last_name':       row[3],
        'nama_lengkap':    f"{row[1]} {row[2]} {row[3]}",
        'country_code':    row[4],
        'mobile_number':   row[5],
        'tanggal_lahir':   row[6],
        'kewarganegaraan': row[7],
    }

    context = {'pengguna': pengguna, 'role': role}

    # MEMBER
    if role == 'member':
        with connection.cursor() as c:
            c.execute("""
                SELECT m.nomor_member, m.tanggal_bergabung,
                       m.award_miles, m.total_miles, t.nama
                FROM member m
                JOIN tier t ON m.id_tier = t.id_tier
                WHERE m.email = %s
            """, [email])
            m = c.fetchone()

        context['member'] = {
            'nomor_member':      m[0],
            'tanggal_bergabung': m[1],
            'award_miles':       m[2] or 0,
            'total_miles':       m[3] or 0,
            'tier':              m[4],
        }

        # Riwayat 5 transaksi terbaru (gabungan transfer + redeem + package + klaim)
        with connection.cursor() as c:
            c.execute("""
                SELECT 'Transfer Keluar' AS tipe, t.timestamp, t.jumlah, p.first_mid_name || ' ' || p.last_name AS keterangan
                FROM transfer t
                JOIN member m2 ON t.email_member_2 = m2.email
                JOIN pengguna p ON m2.email = p.email
                WHERE t.email_member_1 = %s

                UNION ALL

                SELECT 'Transfer Masuk', t.timestamp, t.jumlah, p.first_mid_name || ' ' || p.last_name
                FROM transfer t
                JOIN member m1 ON t.email_member_1 = m1.email
                JOIN pengguna p ON m1.email = p.email
                WHERE t.email_member_2 = %s

                UNION ALL

                SELECT 'Redeem Hadiah', r.timestamp, h.miles, h.nama
                FROM redeem r
                JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah
                WHERE r.email_member = %s

                UNION ALL

                SELECT 'Beli Package', mp.timestamp, amp.jumlah_award_miles, 'Package ' || amp.id
                FROM member_award_miles_package mp
                JOIN award_miles_package amp ON mp.id_award_miles_package = amp.id
                WHERE mp.email_member = %s

                UNION ALL

                SELECT 'Klaim Miles', cm.timestamp, 0, mk.nama_maskapai || ' ' || cm.flight_number
                FROM claim_missing_miles cm
                JOIN maskapai mk ON cm.maskapai = mk.kode_maskapai
                WHERE cm.email_member = %s AND cm.status_penerimaan = 'Disetujui'

                ORDER BY timestamp DESC
                LIMIT 5
            """, [email, email, email, email, email])

            cols = ['tipe', 'timestamp', 'jumlah', 'keterangan']
            context['transaksi'] = [dict(zip(cols, r)) for r in c.fetchall()]

    # STAF 
    elif role == 'staf':
        with connection.cursor() as c:
            c.execute("""
                SELECT s.id_staf, mk.nama_maskapai
                FROM staf s
                JOIN maskapai mk ON s.kode_maskapai = mk.kode_maskapai
                WHERE s.email = %s
            """, [email])
            s = c.fetchone()

        context['staf'] = {
            'id_staf':      s[0],
            'nama_maskapai': s[1],
        }

        # Jumlah klaim menunggu (semua staf)
        with connection.cursor() as c:
            c.execute("SELECT COUNT(*) FROM claim_missing_miles WHERE status_penerimaan = 'Menunggu'")
            context['total_menunggu'] = c.fetchone()[0]

        # Ringkasan klaim milik staf ini
        with connection.cursor() as c:
            c.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE status_penerimaan = 'Disetujui') AS disetujui,
                    COUNT(*) FILTER (WHERE status_penerimaan = 'Ditolak')   AS ditolak
                FROM claim_missing_miles
                WHERE email_staf = %s
            """, [email])
            row = c.fetchone()
            context['klaim_staf'] = {
                'disetujui': row[0],
                'ditolak':   row[1],
            }

    return render(request, 'dashboard/dashboard.html', context)
