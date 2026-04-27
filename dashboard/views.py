from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from member.tier_logic import sync_member_tier


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
        sync_member_tier(email)
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


def pengaturan_profil_view(request):
    email = request.session.get('user_email')
    role = request.session.get('role')
    if not email:
        return redirect('login')

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    with connection.cursor() as c:
        c.execute("""
            SELECT email, password, salutation, first_mid_name, last_name,
                   country_code, mobile_number, tanggal_lahir, kewarganegaraan
            FROM pengguna
            WHERE email = %s
        """, [email])
        row = c.fetchone()

    if not row:
        request.session.flush()
        messages.error(request, 'Data pengguna tidak ditemukan. Silakan login kembali.')
        return redirect('login')

    pengguna = {
        'email': row[0],
        'password_hash': row[1],
        'salutation': row[2],
        'first_mid_name': row[3],
        'last_name': row[4],
        'country_code': row[5],
        'mobile_number': row[6],
        'tanggal_lahir': row[7].strftime('%Y-%m-%d') if row[7] else '',
        'kewarganegaraan': row[8],
        'nama_lengkap': f"{row[2]} {row[3]} {row[4]}",
    }

    context = {
        'role': role,
        'pengguna': pengguna,
        'profile_data': {
            'salutation': pengguna['salutation'],
            'first_mid_name': pengguna['first_mid_name'],
            'last_name': pengguna['last_name'],
            'country_code': pengguna['country_code'],
            'mobile_number': pengguna['mobile_number'],
            'tanggal_lahir': pengguna['tanggal_lahir'],
            'kewarganegaraan': pengguna['kewarganegaraan'],
        },
        'password_data': {},
    }

    if role == 'member':
        with connection.cursor() as c:
            c.execute("""
                SELECT nomor_member, tanggal_bergabung
                FROM member
                WHERE email = %s
            """, [email])
            member = c.fetchone()

        context['member'] = {
            'nomor_member': member[0],
            'tanggal_bergabung': member[1],
        } if member else None

    elif role == 'staf':
        with connection.cursor() as c:
            c.execute("""
                SELECT s.id_staf, s.kode_maskapai, mk.nama_maskapai
                FROM staf s
                JOIN maskapai mk ON s.kode_maskapai = mk.kode_maskapai
                WHERE s.email = %s
            """, [email])
            staf = c.fetchone()

        with connection.cursor() as c:
            c.execute("SELECT kode_maskapai, nama_maskapai FROM maskapai ORDER BY nama_maskapai")
            maskapai_rows = c.fetchall()

        context['staf'] = {
            'id_staf': staf[0],
            'kode_maskapai': staf[1],
            'nama_maskapai': staf[2],
        } if staf else None
        context['maskapai_list'] = [
            {'kode_maskapai': item[0], 'nama_maskapai': item[1]}
            for item in maskapai_rows
        ]
        if staf:
            context['profile_data']['kode_maskapai'] = staf[1]

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            profile_data = {
                'salutation': request.POST.get('salutation', '').strip(),
                'first_mid_name': request.POST.get('first_mid_name', '').strip(),
                'last_name': request.POST.get('last_name', '').strip(),
                'country_code': request.POST.get('country_code', '').strip(),
                'mobile_number': request.POST.get('mobile_number', '').strip(),
                'tanggal_lahir': request.POST.get('tanggal_lahir', '').strip(),
                'kewarganegaraan': request.POST.get('kewarganegaraan', '').strip(),
            }
            if role == 'staf':
                profile_data['kode_maskapai'] = request.POST.get('kode_maskapai', '').strip()

            context['profile_data'] = profile_data

            required_fields = [
                profile_data['salutation'],
                profile_data['first_mid_name'],
                profile_data['last_name'],
                profile_data['country_code'],
                profile_data['mobile_number'],
                profile_data['tanggal_lahir'],
                profile_data['kewarganegaraan'],
            ]
            if role == 'staf':
                required_fields.append(profile_data['kode_maskapai'])

            if not all(required_fields):
                error_message = 'Semua field profil wajib diisi.'
                if is_ajax:
                    return JsonResponse({'ok': False, 'message': error_message}, status=400)
                messages.error(request, error_message)
            else:
                try:
                    with connection.cursor() as c:
                        c.execute("""
                            UPDATE pengguna
                            SET salutation = %s,
                                first_mid_name = %s,
                                last_name = %s,
                                country_code = %s,
                                mobile_number = %s,
                                tanggal_lahir = %s,
                                kewarganegaraan = %s
                            WHERE email = %s
                        """, [
                            profile_data['salutation'],
                            profile_data['first_mid_name'],
                            profile_data['last_name'],
                            profile_data['country_code'],
                            profile_data['mobile_number'],
                            profile_data['tanggal_lahir'],
                            profile_data['kewarganegaraan'],
                            email,
                        ])

                    if role == 'staf':
                        with connection.cursor() as c:
                            c.execute("""
                                UPDATE staf
                                SET kode_maskapai = %s
                                WHERE email = %s
                            """, [profile_data['kode_maskapai'], email])

                    if is_ajax:
                        response_data = {
                            'ok': True,
                            'message': 'Profil berhasil diperbarui.',
                            'pengguna': {
                                'nama_lengkap': f"{profile_data['salutation']} {profile_data['first_mid_name']} {profile_data['last_name']}",
                                'email': email,
                                'country_code': profile_data['country_code'],
                                'mobile_number': profile_data['mobile_number'],
                                'tanggal_lahir': profile_data['tanggal_lahir'],
                                'kewarganegaraan': profile_data['kewarganegaraan'],
                                'initial': (profile_data['first_mid_name'][:1] or '?').upper(),
                            },
                        }
                        if role == 'staf':
                            selected_maskapai = next(
                                (
                                    item['nama_maskapai']
                                    for item in context['maskapai_list']
                                    if item['kode_maskapai'] == profile_data['kode_maskapai']
                                ),
                                profile_data['kode_maskapai'],
                            )
                            response_data['staf'] = {
                                'kode_maskapai': profile_data['kode_maskapai'],
                                'nama_maskapai': selected_maskapai,
                            }
                        return JsonResponse(response_data)

                    messages.success(request, 'Profil berhasil diperbarui.')
                    return redirect('pengaturan_profil')
                except Exception as e:
                    error_message = f'Gagal memperbarui profil: {e}'
                    if is_ajax:
                        return JsonResponse({'ok': False, 'message': error_message}, status=500)
                    messages.error(request, error_message)

        elif action == 'change_password':
            password_data = {
                'old_password': request.POST.get('old_password', ''),
                'new_password': request.POST.get('new_password', ''),
                'confirm_new_password': request.POST.get('confirm_new_password', ''),
            }
            context['password_data'] = password_data

            if not all(password_data.values()):
                error_message = 'Semua field password wajib diisi.'
                if is_ajax:
                    return JsonResponse({'ok': False, 'message': error_message}, status=400)
                messages.error(request, error_message)
            elif not check_password(password_data['old_password'], pengguna['password_hash']):
                error_message = 'Password lama tidak sesuai.'
                if is_ajax:
                    return JsonResponse({'ok': False, 'message': error_message}, status=400)
                messages.error(request, error_message)
            elif password_data['new_password'] != password_data['confirm_new_password']:
                error_message = 'Konfirmasi password baru tidak cocok.'
                if is_ajax:
                    return JsonResponse({'ok': False, 'message': error_message}, status=400)
                messages.error(request, error_message)
            else:
                try:
                    with connection.cursor() as c:
                        c.execute("""
                            UPDATE pengguna
                            SET password = %s
                            WHERE email = %s
                        """, [make_password(password_data['new_password']), email])
                    if is_ajax:
                        return JsonResponse({'ok': True, 'message': 'Password berhasil diubah.'})
                    messages.success(request, 'Password berhasil diubah.')
                    return redirect('pengaturan_profil')
                except Exception as e:
                    error_message = f'Gagal mengubah password: {e}'
                    if is_ajax:
                        return JsonResponse({'ok': False, 'message': error_message}, status=500)
                    messages.error(request, error_message)

    return render(request, 'dashboard/pengaturan_profil.html', context)
