import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse
from .db import (
    get_all_urls,
    get_url_by_id,
    get_checks_by_url_id,
    add_url,
    url_exists,
    add_url_check,
    get_url_id_by_name  # не забудьте добавить эту функцию в модуль db
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


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
        if not is_valid_url(url):
            flash('Некорректный URL')
            return jsonify({'error': 'Некорректный URL'}), 422

        if url_exists(url):
            flash('Страница уже существует')
            existing_url_id = get_url_id_by_name(url)
            return redirect(url_for('view_url', url_id=existing_url_id))

        new_id = add_url(url)
        flash('Страница успешно добавлена')
        return redirect(url_for('view_url', url_id=new_id))

    urls = get_all_urls()
    return render_template('urls.html', urls=urls)


@app.route('/urls/<int:url_id>')
def view_url(url_id):
    url = get_url_by_id(url_id)
    if not url:
        flash('URL не найден')
        return redirect(url_for('urls'))
    checks = get_checks_by_url_id(url_id)
    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:url_id>/checks', methods=['POST'])
def create_check(url_id):
    try:
        url_data = get_url_by_id(url_id)
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

        add_url_check(url_id, status_code, h1, title, description)
        flash('Страница успешно проверена')
    except requests.RequestException:
        flash('Произошла ошибка при проверке')
    return redirect(url_for('view_url', url_id=url_id))
