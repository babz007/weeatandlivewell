from flask import jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
import os
from app.models.blog import Post, PostImage, Comment, db
from datetime import datetime

def init_routes(app):
    # Get all posts
    @app.route('/api/posts', methods=['GET'])
    def get_posts():
        posts = Post.query.order_by(Post.created_at.desc()).all()
        return jsonify([{
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'images': [img.filename for img in post.images],
            'comments': [{
                'id': comment.id,
                'author_name': comment.author_name,
                'content': comment.content,
                'created_at': comment.created_at.isoformat()
            } for comment in post.comments]
        } for post in posts])

    # Create new post
    @app.route('/api/posts', methods=['POST'])
    def create_post():
        try:
            data = request.form
            post = Post(
                title=data['title'],
                content=data['content'],
                author_id=current_user.id
            )
            db.session.add(post)
            db.session.commit()

            # Handle image uploads
            if 'images' in request.files:
                images = request.files.getlist('images')
                for image in images:
                    if image and image.filename:
                        filename = secure_filename(image.filename)
                        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        image.save(image_path)
                        
                        post_image = PostImage(filename=filename, post_id=post.id)
                        db.session.add(post_image)
                db.session.commit()

            return jsonify({
                'message': 'Post created successfully',
                'id': post.id
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Get single post
    @app.route('/api/posts/<int:post_id>', methods=['GET'])
    def get_post(post_id):
        post = Post.query.get_or_404(post_id)
        return jsonify({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'images': [img.filename for img in post.images],
            'comments': [{
                'id': comment.id,
                'author_name': comment.author_name,
                'content': comment.content,
                'created_at': comment.created_at.isoformat()
            } for comment in post.comments]
        })

    # Update post
    @app.route('/api/posts/<int:post_id>', methods=['PUT'])
    def update_post(post_id):
        try:
            post = Post.query.get_or_404(post_id)
            data = request.form
            
            post.title = data['title']
            post.content = data['content']
            
            # Handle new image uploads
            if 'images' in request.files:
                # Delete existing images
                for image in post.images:
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                    db.session.delete(image)
                
                # Add new images
                images = request.files.getlist('images')
                for image in images:
                    if image and image.filename:
                        filename = secure_filename(image.filename)
                        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        image.save(image_path)
                        
                        post_image = PostImage(filename=filename, post_id=post.id)
                        db.session.add(post_image)
            
            db.session.commit()
            return jsonify({'message': 'Post updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Delete post
    @app.route('/api/posts/<int:post_id>', methods=['DELETE'])
    def delete_post(post_id):
        try:
            post = Post.query.get_or_404(post_id)
            
            # Delete associated images from filesystem
            for image in post.images:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
            
            db.session.delete(post)
            db.session.commit()
            return jsonify({'message': 'Post deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Add comment to post
    @app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
    def add_comment(post_id):
        try:
            data = request.get_json()
            comment = Comment(
                author_name=data['author'],
                content=data['content'],
                post_id=post_id
            )
            db.session.add(comment)
            db.session.commit()
            return jsonify({
                'message': 'Comment added successfully',
                'id': comment.id
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Serve uploaded images
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename) 