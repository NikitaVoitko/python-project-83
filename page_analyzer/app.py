import os
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use a secure and unique secret key


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=['GET', 'POST'])
def urls():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    if request.method == 'POST':
        url = request.form['url']
        if len(url) > 255:
            flash('URL слишком длинный')
            conn.close()
            return redirect(url_for('index'))

        cursor.execute('SELECT * FROM urls WHERE name = %s', (url,))
        existing_url = cursor.fetchone()
        if existing_url:
            flash('URL уже существует')
            conn.close()
            return redirect(url_for('index'))

        cursor.execute(
            'INSERT INTO urls (name) VALUES (%s) RETURNING id',
            (url,)
        )
        new_id = cursor.fetchone()['id']
        conn.commit()
        conn.close()
        flash('URL успешно добавлен')
        return redirect(url_for('view_url', url_id=new_id))

    cursor.execute('''
        SELECT urls.*, max(url_checks.created_at) AS last_checked,
        max(url_checks.status_code) AS last_status_code
        FROM urls
        LEFT JOIN url_checks ON urls.id = url_checks.url_id
        GROUP BY urls.id
        ORDER BY last_checked DESC NULLS LAST
    ''')
    urls = cursor.fetchall()
    conn.close()
    return render_template('urls.html', urls=urls)


@app.route('/urls/<int:url_id>')
def view_url(url_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM urls WHERE id = %s', (url_id,))
    url = cursor.fetchone()
    if not url:
        flash('URL не найден')
        conn.close()
        return redirect(url_for('urls'))
    cursor.execute(
     'SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC',
     (url_id,)
     )
    checks = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:url_id>/checks', methods=['POST'])
def create_check(url_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute('SELECT name FROM urls WHERE id = %s', (url_id,))
        url_data = cursor.fetchone()
        url = url_data['name']

        response = requests.get(url)
        response.raise_for_status()
        status_code = response.status_code

        soup = BeautifulSoup(response.text, 'html.parser')
        h1 = soup.h1.string if soup.h1 else None
        title = soup.title.string if soup.title else None
        description = None
        description_meta = soup.find('meta', attrs={'name': 'description'})
        if description_meta:
            description = description_meta.get('content')

        cursor.execute(
         'INSERT INTO url_checks (url_id, status_code, h1, title, description)'
         'VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at',
         (url_id, status_code, h1, title, description)
         )
        check_id, created_at = cursor.fetchone()
        conn.commit()
        flash('Check created successfully!')
    except requests.RequestException:
        flash('Произошла ошибка при проверке')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('view_url', url_id=url_id))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
