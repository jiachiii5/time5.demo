from flask import Blueprint, render_template
from app.models.record import get_all_records, get_record

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/history')
def history():
    records = get_all_records()
    return render_template('history.html', records=records)

@bp.route('/result/<int:id>')
def result(id):
    record = get_record(id)
    if not record:
        return "Record not found", 404
    return render_template('result.html', record=record)
