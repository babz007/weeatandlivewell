# scripts/initialize_db.py

import os
from app import create_app, db
from app.models.blog import AdminUser, Post
from sqlalchemy import text
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    try:
        print("🔧 Creating tables...")
        db.create_all()

        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('post')]

        if 'category' not in columns:
            print("➕ Adding 'category' column to post table")
            db.session.execute(text('ALTER TABLE post ADD COLUMN category VARCHAR(50)'))

        if 'status' not in columns:
            print("➕ Adding 'status' column to post table")
            db.session.execute(text("ALTER TABLE post ADD COLUMN status VARCHAR(20) DEFAULT 'draft'"))

        if not AdminUser.query.filter_by(username='admin').first():
            print("👤 Creating default admin user")
            admin_user = AdminUser(
                username='admin',
                password_hash=generate_password_hash('admin', method='pbkdf2:sha256')
            )
            db.session.add(admin_user)
            db.session.commit()

        print("✅ DB initialized successfully.")

    except Exception as e:
        print("❌ Error initializing database:", str(e))