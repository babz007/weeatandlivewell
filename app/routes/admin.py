from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from app.models.blog import AdminUser, Post, Comment
from app import db
from datetime import datetime, timedelta
from functools import wraps

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
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required', 'error')
            return render_template('admin/post_editor.html')
        
        post = Post(title=title, content=content)
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully', 'success')
        return redirect(url_for('admin.posts'))
    
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
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        db.session.commit()
        
        flash('Post updated successfully', 'success')
        return redirect(url_for('admin.posts'))
    
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