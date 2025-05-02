import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, static_folder=os.path.join(app.root_path, '..', 'public'))
    app.config.from_object(Config)

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'admin.login'

    # Import models after db is initialized
    from app.models.blog import AdminUser, Post

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    # Register blueprints
    from app.routes.admin import admin
    app.register_blueprint(admin, url_prefix='/admin')

    from app.routes.blog import init_routes
    init_routes(app)

    # Serve public static files
    @app.route('/')
    def home():
        return send_from_directory(os.path.join(app.root_path, '..', 'public'), 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(os.path.join(app.root_path, '..', 'public'), path)

    # Health check route
    @app.route("/health")
    def health_check():
        try:
            db.session.execute("SELECT 1")
            return {"status": "ok", "db": "connected"}
        except Exception as e:
            return {"status": "error", "db": str(e)}, 500

    # Run database initialization and one-time setup
    with app.app_context():
        _initialize_database()

    return app


def _initialize_database():
    """Create tables and seed default admin if needed."""
    from app.models.blog import AdminUser
    from werkzeug.security import generate_password_hash

    try:
        db.create_all()

        # Manually add missing columns (consider switching to Flask-Migrate long term)
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('post')]
        if 'category' not in columns:
            db.engine.execute('ALTER TABLE post ADD COLUMN category VARCHAR(50)')
        if 'status' not in columns:
            db.engine.execute("ALTER TABLE post ADD COLUMN status VARCHAR(20) DEFAULT 'draft'")

        # Seed default admin user
        if not AdminUser.query.filter_by(username='admin').first():
            admin_user = AdminUser(
                username='admin',
                password_hash=generate_password_hash('admin', method='pbkdf2:sha256')
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Default admin user created.")
    except Exception as e:
        print(f"⚠️ Database init failed: {e}")