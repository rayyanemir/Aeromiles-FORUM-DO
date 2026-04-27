from django.db import connection


def get_eligible_tier(total_miles, cursor=None):
    owns_cursor = cursor is None
    if owns_cursor:
        cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT id_tier, nama, minimal_tier_miles
            FROM tier
            WHERE minimal_tier_miles <= %s
            ORDER BY minimal_tier_miles DESC, minimal_frekuensi_terbang DESC
            LIMIT 1
        """, [total_miles])
        row = cursor.fetchone()
    finally:
        if owns_cursor:
            cursor.close()

    if not row:
        return None

    return {
        'id_tier': row[0],
        'nama': row[1],
        'minimal_tier_miles': row[2],
    }


def sync_member_tier(email, cursor=None):
    owns_cursor = cursor is None
    if owns_cursor:
        cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT m.id_tier, COALESCE(m.total_miles, 0), t.nama
            FROM member m
            JOIN tier t ON m.id_tier = t.id_tier
            WHERE m.email = %s
        """, [email])
        member_row = cursor.fetchone()

        if not member_row:
            return None

        previous_tier = {
            'id_tier': member_row[0],
            'nama': member_row[2],
        }
        total_miles = member_row[1]

        eligible_tier = get_eligible_tier(total_miles, cursor=cursor)
        if not eligible_tier:
            return {
                'updated': False,
                'previous_tier': previous_tier,
                'current_tier': previous_tier,
                'total_miles': total_miles,
            }

        if eligible_tier['id_tier'] != previous_tier['id_tier']:
            cursor.execute("""
                UPDATE member
                SET id_tier = %s
                WHERE email = %s
            """, [eligible_tier['id_tier'], email])

            return {
                'updated': True,
                'previous_tier': previous_tier,
                'current_tier': {
                    'id_tier': eligible_tier['id_tier'],
                    'nama': eligible_tier['nama'],
                },
                'total_miles': total_miles,
            }

        return {
            'updated': False,
            'previous_tier': previous_tier,
            'current_tier': previous_tier,
            'total_miles': total_miles,
        }
    finally:
        if owns_cursor:
            cursor.close()
