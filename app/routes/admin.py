from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user, login_user, logout_user
from app.models.blog import AdminUser, Post, Comment, PostImage
from app import db, csrf
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure uploads directory exists
UPLOAD_FOLDER = os.path.join('public', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    logger.info(f"Created uploads directory at: {UPLOAD_FOLDER}")

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, AdminUser):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/register', methods=['GET', 'POST'])
def register():
    # Check if any admin user exists
    if AdminUser.query.first() and not os.getenv('ALLOW_ADMIN_REGISTRATION', '').lower() == 'true':
        flash('Admin registration is disabled.', 'danger')
        return redirect(url_for('admin.login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        registration_key = request.form.get('registration_key')

        # Validate registration key
        if registration_key != os.getenv('ADMIN_REGISTRATION_KEY'):
            flash('Invalid registration key.', 'danger')
            return render_template('admin/register.html')

        # Validate password
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('admin/register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('admin/register.html')

        # Check if username exists
        if AdminUser.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('admin/register.html')

        # Create new admin user
        try:
            new_admin = AdminUser(
                username=username,
                password_hash=generate_password_hash(password, method='pbkdf2:sha256')
            )
            db.session.add(new_admin)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('admin.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration.', 'danger')
            return render_template('admin/register.html')

    return render_template('admin/register.html')

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('admin/login.html')
        
        user = AdminUser.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        
        flash('Invalid username or password.', 'danger')
    
    return render_template('admin/login.html')

@admin.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin.login'))

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    stats = {
        'total_posts': Post.query.count(),
        'total_comments': Comment.query.count(),
        'total_subscribers': 0  # Add subscriber count if you have a subscribers table
    }
    
    # Get recent activity
    recent_activity = []
    
    # Add recent posts
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    for post in recent_posts:
        recent_activity.append({
            'icon': 'file-alt',
            'text': f'New post created: {post.title}',
            'time': post.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    # Add recent comments
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    for comment in recent_comments:
        recent_activity.append({
            'icon': 'comment',
            'text': f'New comment by {comment.author_name} on {comment.post.title}',
            'time': comment.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    # Sort activities by time
    recent_activity.sort(key=lambda x: x['time'], reverse=True)
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_activity=recent_activity[:10],
                         recent_posts=recent_posts)

@admin.route('/posts/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_post():
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title')
            content = request.form.get('content')
            
            logger.debug(f"Creating new post. Title: {title}")
            logger.debug(f"Content length: {len(content) if content else 0}")
            logger.debug(f"Form data: {request.form}")
            logger.debug(f"Files: {request.files}")
            
            if not title or not content:
                logger.error("Missing title or content")
                logger.error(f"Title: {title}")
                logger.error(f"Content: {content}")
                flash('Title and content are required', 'error')
                return render_template('admin/post_editor.html')
            
            # Create new post
            post = Post(
                title=title,
                content=content,
                author_id=current_user.id,
                category=request.form.get('category'),
                status=request.form.get('status', 'draft')
            )
            logger.debug(f"Created Post object: {post}")
            
            db.session.add(post)
            db.session.commit()
            logger.debug(f"Post saved to database. ID: {post.id}")

            # Handle image uploads
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename:
                    logger.debug(f"Processing image upload: {image.filename}")
                    filename = secure_filename(image.filename)
                    image_path = os.path.join(UPLOAD_FOLDER, filename)
                    logger.debug(f"Saving image to: {image_path}")
                    
                    # Ensure the uploads directory exists
                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)
                        logger.info(f"Created uploads directory at: {UPLOAD_FOLDER}")
                    
                    image.save(image_path)
                    logger.debug(f"Image saved successfully to: {image_path}")
                    
                    post_image = PostImage(filename=filename, post_id=post.id)
                    logger.debug(f"Created PostImage object: {post_image}")
                    db.session.add(post_image)
                    db.session.commit()
                    logger.debug("Image saved to database")

            flash('Post created successfully', 'success')
            logger.info(f"Successfully created post with ID: {post.id}")
            return redirect(url_for('admin.posts'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating post: {str(e)}", exc_info=True)
            flash(f'Error creating post: {str(e)}', 'error')
            return render_template('admin/post_editor.html')
    
    return render_template('admin/post_editor.html')

@admin.route('/posts')
@login_required
@admin_required
def posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('admin/posts.html', posts=posts)

@admin.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    logger.debug(f"Editing post ID: {post_id}")
    
    if request.method == 'POST':
        try:
            new_title = request.form.get('title')
            new_content = request.form.get('content')
            
            logger.debug(f"Updating post. New title: {new_title}")
            logger.debug(f"New content length: {len(new_content) if new_content else 0}")
            
            post.title = new_title
            post.content = new_content
            
            # Handle image uploads
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename:
                    logger.debug(f"Processing image upload: {image.filename}")
                    filename = secure_filename(image.filename)
                    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    logger.debug(f"Saving image to: {image_path}")
                    image.save(image_path)
                    
                    # Delete old images
                    for old_image in post.images:
                        logger.debug(f"Deleting old image: {old_image.filename}")
                        old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_image.filename)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                        db.session.delete(old_image)
                    
                    # Add new image
                    post_image = PostImage(filename=filename, post_id=post.id)
                    logger.debug(f"Created new PostImage object: {post_image}")
                    db.session.add(post_image)
            
            db.session.commit()
            logger.info(f"Successfully updated post ID: {post_id}")
            flash('Post updated successfully', 'success')
            return redirect(url_for('admin.posts'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating post: {str(e)}", exc_info=True)
            flash(f'Error updating post: {str(e)}', 'error')
            return render_template('admin/post_editor.html', post=post)
    
    return render_template('admin/post_editor.html', post=post)

@admin.route('/posts/<int:post_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'success': True})

@admin.route('/comments')
@login_required
@admin_required
def comments():
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.order_by(Comment.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/comments.html', comments=comments)

@admin.route('/comments/<int:comment_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'success': True})

@admin.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.email = request.form.get('email')
        
        new_password = request.form.get('new_password')
        if new_password:
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Settings updated successfully', 'success')
    
    return render_template('admin/settings.html')

@admin.route('/dbcheck')
@login_required
@admin_required
def check_db():
    try:
        # Get database URL (with password masked)
        db_url = str(db.engine.url)
        if 'postgresql://' in db_url:
            # Mask the password in the URL
            parts = db_url.split('@')
            if len(parts) > 1:
                credentials = parts[0].split(':')
                if len(credentials) > 2:
                    masked_url = f"{credentials[0]}:****@{parts[1]}"
                else:
                    masked_url = db_url
            else:
                masked_url = db_url
        else:
            masked_url = db_url

        # Get all table names
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Get counts and data
        users = AdminUser.query.all()
        posts = Post.query.all()
        
        return jsonify({
            'status': 'success',
            'database_url': masked_url,
            'tables': tables,
            'user_count': len(users),
            'post_count': len(posts),
            'users': [{
                'id': user.id,
                'username': user.username,
                'created_at': user.created_at.isoformat() if user.created_at else None
            } for user in users],
            'posts': [{
                'id': post.id,
                'title': post.title,
                'author_id': post.author_id,
                'created_at': post.created_at.isoformat() if post.created_at else None,
                'category': post.category,
                'status': post.status
            } for post in posts]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 