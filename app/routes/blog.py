from flask import jsonify, request
from werkzeug.utils import secure_filename
import os
from app.models.blog import Post, PostImage, Comment, db

def init_routes(app):
    @app.route('/api/posts', methods=['GET'])
    def get_posts():
        posts = Post.query.order_by(Post.date_posted.desc()).all()
        return jsonify([{
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'date_posted': post.date_posted.isoformat(),
            'images': [img.filename for img in post.images],
            'comments': [{
                'id': comment.id,
                'author': comment.author,
                'content': comment.content,
                'date_posted': comment.date_posted.isoformat()
            } for comment in post.comments]
        } for post in posts])

    @app.route('/api/posts', methods=['POST'])
    def create_post():
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        
        data = request.form
        post = Post(
            title=data['title'],
            content=data['content']
        )
        db.session.add(post)
        db.session.commit()

        # Handle image uploads
        images = request.files.getlist('images')
        for image in images:
            if image and image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                
                post_image = PostImage(filename=filename, post_id=post.id)
                db.session.add(post_image)
        
        db.session.commit()
        return jsonify({'message': 'Post created successfully', 'id': post.id}), 201

    @app.route('/api/posts/<int:post_id>', methods=['GET'])
    def get_post(post_id):
        post = Post.query.get_or_404(post_id)
        return jsonify({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'date_posted': post.date_posted.isoformat(),
            'image_url': post.images[0].filename if post.images else None,
            'comments': [{
                'id': comment.id,
                'author': comment.author,
                'content': comment.content,
                'date_posted': comment.date_posted.isoformat()
            } for comment in post.comments]
        })

    @app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
    def add_comment(post_id):
        data = request.get_json()
        comment = Comment(
            author=data['author'],
            content=data['content'],
            post_id=post_id
        )
        db.session.add(comment)
        db.session.commit()
        return jsonify({'message': 'Comment added successfully', 'id': comment.id}), 201 