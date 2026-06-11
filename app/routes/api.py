import os
import uuid
import random
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.services.stt_service import transcribe_audio
from app.services.image_service import generate_image
from app.models.record import create_record, update_record_image, get_record, search_records, get_db

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
        
        # 2. Extract unlock configuration
        unlock_type = request.form.get('unlock_type', 'none')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        radius = request.form.get('radius')
        location_name = request.form.get('location_name', '').strip()
        random_min_hours = request.form.get('random_min_hours')
        random_max_hours = request.form.get('random_max_hours')

        is_locked = 0
        delivery_time = None

        if unlock_type == 'geofence':
            is_locked = 1
            latitude = float(latitude) if latitude else None
            longitude = float(longitude) if longitude else None
            radius = float(radius) if radius else 100.0
        elif unlock_type == 'random':
            is_locked = 1
            min_h = float(random_min_hours) if random_min_hours else 1.0
            max_h = float(random_max_hours) if random_max_hours else 24.0
            delay_hours = random.uniform(min_h, max_h)
            delivery_time = (datetime.now() + timedelta(hours=delay_hours)).strftime("%Y-%m-%d %H:%M:%S")
            random_min_hours = int(min_h)
            random_max_hours = int(max_h)
        else:
            unlock_type = 'none'
            latitude = None
            longitude = None
            radius = None
            location_name = None
            random_min_hours = None
            random_max_hours = None

        # 3. Save to DB with unlock conditions
        record_id = create_record(
            relative_path, transcribed_text, 
            unlock_type=unlock_type, 
            latitude=latitude, 
            longitude=longitude, 
            radius=radius, 
            location_name=location_name, 
            is_locked=is_locked, 
            delivery_time=delivery_time, 
            random_min_hours=random_min_hours, 
            random_max_hours=random_max_hours
        )
        
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

@bp.route('/unlock', methods=['POST'])
def unlock_record():
    data = request.json or {}
    record_id = data.get('record_id')
    user_lat = data.get('latitude')
    user_lng = data.get('longitude')
    bypass = data.get('bypass', False)

    if not record_id:
        return jsonify({'error': 'Missing record_id'}), 400

    db = get_db()
    record = db.execute('SELECT * FROM records WHERE id = ?', (record_id,)).fetchone()
    if not record:
        return jsonify({'error': 'Record not found'}), 404

    if record['is_locked'] == 0:
        return jsonify({'success': True, 'unlocked': True, 'message': 'Already unlocked'})

    if bypass:
        db.execute('UPDATE records SET is_locked = 0 WHERE id = ?', (record_id,))
        db.commit()
        return jsonify({'success': True, 'unlocked': True, 'message': 'Bypassed lock successfully'})

    if record['unlock_type'] == 'geofence':
        import math
        try:
            lat1 = float(user_lat)
            lon1 = float(user_lng)
            lat2 = float(record['latitude'])
            lon2 = float(record['longitude'])
            radius = float(record['radius'])
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid coordinates provided'}), 400

        # Haversine formula
        R = 6371000.0  # meters
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = (math.sin(dLat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dLon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        if distance <= radius:
            db.execute('UPDATE records SET is_locked = 0 WHERE id = ?', (record_id,))
            db.commit()
            return jsonify({
                'success': True,
                'unlocked': True,
                'distance': round(distance, 1),
                'message': f'Unlocked! Distance: {round(distance, 1)}m (inside {radius}m radius)'
            })
        else:
            return jsonify({
                'success': False,
                'unlocked': False,
                'distance': round(distance, 1),
                'radius': radius,
                'message': f'Still locked. Distance is {round(distance, 1)}m, must be within {radius}m.'
            })

    elif record['unlock_type'] == 'random':
        dt = record['delivery_time']
        if isinstance(dt, str):
            try:
                dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    dt = None
        
        if dt and datetime.now() >= dt:
            db.execute('UPDATE records SET is_locked = 0 WHERE id = ?', (record_id,))
            db.commit()
            return jsonify({'success': True, 'unlocked': True, 'message': 'Unlocked'})
        else:
            remaining = (dt - datetime.now()).total_seconds() if dt else 0
            return jsonify({
                'success': False,
                'unlocked': False,
                'remaining_seconds': max(0, remaining),
                'message': 'Still locked. Time has not elapsed.'
            })

    return jsonify({'error': 'Invalid unlock type'}), 400

