from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.models.blog import db, AdminUser
from app.routes.blog import init_routes
from app.routes.admin import admin
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, static_folder='../public')
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = os.path.join('public', 'uploads')
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(admin, url_prefix='/admin')

    # Initialize routes
    init_routes(app)

    # Static file serving
    @app.route('/')
    def home():
        return send_from_directory('../public', 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory('../public', path)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app 