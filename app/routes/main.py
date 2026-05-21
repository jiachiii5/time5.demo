from flask import Blueprint, render_template, request
from app.models.record import get_all_records, get_record, search_records

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/history')
def history():
    q = request.args.get('q', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    
    if q or start_date or end_date:
        records = search_records(query=q, start_date=start_date, end_date=end_date)
    else:
        records = get_all_records()
        
    return render_template(
        'history.html', 
        records=records, 
        q=q, 
        start_date=start_date, 
        end_date=end_date
    )

@bp.route('/result/<int:id>')
def result(id):
    record = get_record(id)
    if not record:
        return "Record not found", 404
    return render_template('result.html', record=record)

