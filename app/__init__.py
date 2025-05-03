from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from sqlalchemy import text
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, static_folder='../public')
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = os.path.join('public', 'uploads')
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY', os.environ.get('SECRET_KEY', 'dev'))

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

    # Initialize routes
    from app.routes.blog import init_routes
    init_routes(app)

    # Static file serving
    @app.route('/')
    def home():
        return send_from_directory('../public', 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory('../public', path)

    # Create database tables if they don't exist
    with app.app_context():
        try:
            # Create all tables first
            db.create_all()
            
            # Add new columns using SQLAlchemy metadata
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('post')]
            
            if 'category' not in columns:
                db.engine.execute('ALTER TABLE post ADD COLUMN category VARCHAR(50)')
            if 'status' not in columns:
                db.engine.execute('ALTER TABLE post ADD COLUMN status VARCHAR(20) DEFAULT \'draft\'')
            
            # Create default admin user if it doesn't exist
            from werkzeug.security import generate_password_hash
            if not AdminUser.query.filter_by(username='admin').first():
                admin_user = AdminUser(
                    username='admin',
                    password_hash=generate_password_hash('admin', method='pbkdf2:sha256')
                )
                db.session.add(admin_user)
                db.session.commit()
                print("Default admin user created successfully")
        except Exception as e:
            print(f"Error during database initialization: {str(e)}")
            # Don't raise the exception, allow the app to start anyway

    @app.route("/health")
    def health_check():
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "ok", "db": "connected"}
        except Exception as e:
            return {"status": "error", "db": str(e)}, 500

    return app 