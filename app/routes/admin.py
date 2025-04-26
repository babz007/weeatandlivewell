from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user, login_user, logout_user
from app.models.blog import AdminUser, Post, Comment, PostImage
from app import db
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
import os
import logging

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

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('admin/login.html')
        
        user = AdminUser.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('admin.dashboard'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html')

@admin.route('/logout')
@login_required
def logout():
    logout_user()
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
    recent_posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    for post in recent_posts:
        recent_activity.append({
            'icon': 'file-alt',
            'text': f'New post created: {post.title}',
            'time': post.date_posted.strftime('%Y-%m-%d %H:%M')
        })
    
    # Add recent comments
    recent_comments = Comment.query.order_by(Comment.date_posted.desc()).limit(5).all()
    for comment in recent_comments:
        recent_activity.append({
            'icon': 'comment',
            'text': f'New comment by {comment.author} on {comment.post.title}',
            'time': comment.date_posted.strftime('%Y-%m-%d %H:%M')
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
                date_posted=datetime.utcnow()
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
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
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
    comments = Comment.query.order_by(Comment.date_posted.desc()).paginate(page=page, per_page=20)
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