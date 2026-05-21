import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.services.stt_service import transcribe_audio
from app.services.image_service import generate_image
from app.models.record import create_record, update_record_image, get_record, search_records

bp = Blueprint('api', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'webm'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio part'}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and (allowed_file(file.filename) or file.filename == 'blob'): # Web audio API sends blob
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'webm'
        filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 1. Transcribe audio
        relative_path = f"uploads/{filename}"
        transcribed_text = transcribe_audio(filepath)
        
        # 2. Save to DB initially without image
        record_id = create_record(relative_path, transcribed_text)
        
        return jsonify({
            'success': True,
            'record_id': record_id,
            'transcribed_text': transcribed_text,
            'audio_url': f"/static/{relative_path}"
        })
        
    return jsonify({'error': 'Invalid file type'}), 400

@bp.route('/generate', methods=['POST'])
def generate():
    data = request.json
    record_id = data.get('record_id')
    prompt = data.get('prompt')
    
    if not record_id or not prompt:
        return jsonify({'error': 'Missing record_id or prompt'}), 400
        
    # Generate Image
    image_url = generate_image(prompt)
    
    # Update DB
    update_record_image(record_id, image_url)
    
    return jsonify({
        'success': True,
        'image_url': image_url
    })

@bp.route('/search', methods=['GET'])
def api_search():
    q = request.args.get('q', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    
    records = search_records(query=q, start_date=start_date, end_date=end_date)
    
    results = []
    for r in records:
        results.append({
            'id': r['id'],
            'audio_path': r['audio_path'],
            'transcribed_text': r['transcribed_text'],
            'image_path': r['image_path'],
            'created_at': r['created_at'].isoformat() if hasattr(r['created_at'], 'isoformat') else str(r['created_at'])
        })
        
    return jsonify({
        'success': True,
        'records': results
    })

