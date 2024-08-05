import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def get_all_urls():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('''
        SELECT urls.*, max(url_checks.created_at) AS last_checked,
        max(url_checks.status_code) AS last_status_code
        FROM urls
        LEFT JOIN url_checks ON urls.id = url_checks.url_id
        GROUP BY urls.id
        ORDER BY last_checked DESC NULLS LAST
    ''')
    urls = cursor.fetchall()
    cursor.close()
    conn.close()
    return urls


def get_url_by_id(url_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM urls WHERE id = %s', (url_id,))
    url = cursor.fetchone()
    cursor.close()
    conn.close()
    return url


def get_checks_by_url_id(url_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
     'SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC',
     (url_id,)
     )
    checks = cursor.fetchall()
    cursor.close()
    conn.close()
    return checks


def add_url(name):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        'INSERT INTO urls (name) VALUES (%s) RETURNING id',
        (name,)
    )
    new_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return new_id


def url_exists(name):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM urls WHERE name = %s', (name,))
    existing_url = cursor.fetchone()
    cursor.close()
    conn.close()
    return existing_url


def add_url_check(url_id, status_code, h1, title, description):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
     'INSERT INTO url_checks (url_id, status_code, h1, title, description)'
     'VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at',
     (url_id, status_code, h1, title, description)
     )
    check_id, created_at = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return check_id, created_at
