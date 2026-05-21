import os
from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'database.db'),
        UPLOAD_FOLDER=os.path.join(app.root_path, 'static', 'uploads'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024 # 16 MB max
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # Ensure instance and upload folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from .routes import main, api, collaboration
    from .models.record import close_db
    
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(collaboration.bp, url_prefix='/collaboration')

    # Register DB teardown
    app.teardown_appcontext(close_db)

    # Context processor to inject current user globally
    from flask import session
    from app.models.record import get_db

    @app.context_processor
    def inject_user():
        user = None
        if 'user_id' in session:
            try:
                db = get_db()
                user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            except Exception:
                pass
        return dict(current_user=user)

    return app
