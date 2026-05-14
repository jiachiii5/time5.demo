import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize DB (run once on start for simplicity)
    from app.models.record import init_db
    with app.app_context():
        init_db()
        
    app.run(debug=True, port=5000)
