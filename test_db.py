import psycopg
try:
    conn = psycopg.connect('postgresql://postgres:MATArani%2424680%23@db.ntpwefohvfdwygdolaqv.supabase.co:5432/postgres')
    print('Success without brackets')
    conn.close()
except Exception as e:
    print('Failed without brackets:', e)

try:
    conn = psycopg.connect('postgresql://postgres:%5BMATArani%2424680%23%5D@db.ntpwefohvfdwygdolaqv.supabase.co:5432/postgres')
    print('Success with brackets')
    conn.close()
except Exception as e:
    print('Failed with brackets:', e)
