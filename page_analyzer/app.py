import os
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Для использования flash сообщений


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=['GET', 'POST'])
def urls():
    if request.method == 'POST':
        url = request.form['url']
        if len(url) > 255:
            flash('URL слишком длинный')
            return redirect(url_for('index'))

        cursor.execute('SELECT * FROM urls WHERE name = %s', (url,))
        existing_url = cursor.fetchone()
        if existing_url:
            flash('URL уже существует')
            return redirect(url_for('index'))

        cursor.execute(
         'INSERT INTO urls (name) VALUES (%s) RETURNING id',
         (url,)
        )
        new_id = cursor.fetchone()['id']
        conn.commit()
        flash('URL успешно добавлен')
        return redirect(url_for('show_url', id=new_id))

    cursor.execute('SELECT * FROM urls ORDER BY created_at DESC')
    urls = cursor.fetchall()
    return render_template('urls.html', urls=urls)


@app.route('/urls/<int:id>')
def show_url(id):
    cursor.execute('SELECT * FROM urls WHERE id = %s', (id,))
    url = cursor.fetchone()
    if not url:
        flash('URL не найден')
        return redirect(url_for('urls'))
    return render_template('url.html', url=url)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
