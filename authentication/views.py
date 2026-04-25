from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password

def register_view(request):
    # Selalu ambil maskapai_list untuk dropdown staf
    with connection.cursor() as cursor:
        cursor.execute("SELECT kode_maskapai, nama_maskapai FROM maskapai ORDER BY nama_maskapai")
        maskapai_list = [{'kode_maskapai': r[0], 'nama_maskapai': r[1]} for r in cursor.fetchall()]

    if request.method == "POST":
        data = request.POST
        email           = data.get('email')
        password        = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            return render(request, 'authentication/register.html', {
                'error': 'Password tidak cocok',
                'maskapai_list': maskapai_list
            })

        hashed_pw = make_password(password)

        try:
            with connection.cursor() as cursor:
                # Cek duplikat email
                cursor.execute("SELECT email FROM pengguna WHERE email = %s", [email])
                if cursor.fetchone():
                    return render(request, 'authentication/register.html', {
                        'error': 'Email sudah terdaftar.',
                        'maskapai_list': maskapai_list
                    })

                # Insert PENGGUNA
                cursor.execute("""
                    INSERT INTO pengguna (email, password, salutation, first_mid_name, last_name,
                    country_code, mobile_number, tanggal_lahir, kewarganegaraan)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    email, hashed_pw,
                    data.get('salutation'),
                    data.get('first_mid_name'),   # ← sesuai nama field di HTML
                    data.get('last_name'),
                    data.get('country_code'),
                    data.get('mobile_number'),    # ← sesuai nama field di HTML
                    data.get('tanggal_lahir'),    # ← sesuai nama field di HTML
                    data.get('kewarganegaraan')
                ])

                role = data.get('role')
                if role == 'member':
                    with connection.cursor() as c1:
                        c1.execute("SELECT nomor_member FROM member ORDER BY nomor_member DESC LIMIT 1")
                        last = c1.fetchone()
                        next_num = int(last[0][1:]) + 1 if last else 1
                        nomor_member = f"M{next_num:04d}"
                    with connection.cursor() as c2:
                        c2.execute("SELECT id_tier FROM tier ORDER BY minimal_tier_miles ASC LIMIT 1")
                        tier_row = c2.fetchone()
                        id_tier = tier_row[0] if tier_row else None

                    print(f"DEBUG: email={email}, nomor={nomor_member}, tier={id_tier}") #buat debugging

                    with connection.cursor() as c3:
                        c3.execute("""
                            INSERT INTO member (email, nomor_member, tanggal_bergabung, id_tier, award_miles, total_miles)
                            VALUES (%s, %s, CURRENT_DATE, %s, 0, 0)
                        """, [email, nomor_member, id_tier])

                else:  # staf
                    with connection.cursor() as c1:
                        c1.execute("SELECT id_staf FROM staf ORDER BY id_staf DESC LIMIT 1")
                        last = c1.fetchone()
                        next_num = int(last[0][1:]) + 1 if last else 1
                        id_staf = f"S{next_num:04d}"

                    with connection.cursor() as c2:
                        c2.execute("""
                            INSERT INTO staf (email, id_staf, kode_maskapai)
                            VALUES (%s, %s, %s)
                        """, [email, id_staf, data.get('kode_maskapai')])

            messages.success(request, "Registrasi berhasil! Silakan login.")
            return redirect('login')

        except Exception as e:
            return render(request, 'authentication/register.html', {
                'error': f"Gagal mendaftar: {e}",
                'maskapai_list': maskapai_list
            })

    return render(request, 'authentication/register.html', {'maskapai_list': maskapai_list})


def login_view(request):
    if request.method == "POST":
        email    = request.POST.get('email')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            cursor.execute("SELECT email, password FROM pengguna WHERE email = %s", [email])
            user = cursor.fetchone()

        if user and check_password(password, user[1]):
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM member WHERE email = %s", [email])
                role = 'member' if cursor.fetchone() else 'staf'

            request.session['user_email'] = email
            request.session['role'] = role
            return redirect('dashboard')
        else:
            return render(request, 'authentication/login.html', {
                'error': 'Email atau password salah.',
                'email': email
            })

    return render(request, 'authentication/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')