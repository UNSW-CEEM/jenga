from application import app
from flask import render_template

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/available_dates')
def available_dates():
    return []

