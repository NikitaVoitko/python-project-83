# Makefile

install:
	poetry install

run:
	poetry run flask --app page_analyzer.app:app run

lint:
	poetry run flake8 page_analyzer

PORT ?= 8000

start:
	poetry run gunicorn --chdir code -w 5 -b 0.0.0.0:8001 page_analyzer:app
	
build:
	bash page_analyzer/scripts/build.sh