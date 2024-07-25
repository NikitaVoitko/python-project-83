import os
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

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
        SELECT urls.*, max(url_checks.created_at) AS last_checked 
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
    cursor.execute('SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC', (url_id,))
    checks = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('url.html', url=url, checks=checks)

@app.route('/urls/<int:url_id>/checks', methods=['POST'])
def create_check(url_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO url_checks (url_id) VALUES (%s) RETURNING id, created_at',
        (url_id,)
    )
    check_id, created_at = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    flash('Check created successfully!')
    return redirect(url_for('view_url', url_id=url_id))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)