from django.db import connection


def nav_user(request):
    email = request.session.get('user_email')
    role = request.session.get('role')

    if not email or not role:
        return {}

    with connection.cursor() as c:
        c.execute("""
            SELECT salutation, first_mid_name, last_name
            FROM pengguna
            WHERE email = %s
        """, [email])
        row = c.fetchone()

    if not row:
        return {}

    salutation, first_mid_name, last_name = row
    first_mid_name = first_mid_name or ''
    last_name = last_name or ''

    return {
        'nav_user': {
            'email': email,
            'role': role,
            'initial': (first_mid_name[:1] or '?').upper(),
            'nama_lengkap': f"{salutation} {first_mid_name} {last_name}".strip(),
        }
    }
