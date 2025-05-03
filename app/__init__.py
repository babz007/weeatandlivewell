from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, static_folder='../public')
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'admin.login'

    # Import models
    from app.models.blog import AdminUser, Post

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    # Register blueprints
    from app.routes.admin import admin
    app.register_blueprint(admin, url_prefix='/admin')

    from app.routes.blog import init_routes
    init_routes(app)

    # Static file serving
    @app.route('/')
    def home():
        return send_from_directory(os.path.join(app.root_path, '../public'), 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(os.path.join(app.root_path, '../public'), path)

    @app.route("/health")
    def health_check():
        from sqlalchemy import text
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "ok", "db": "connected"}
        except Exception as e:
            return {"status": "error", "db": str(e)}, 500

    return app