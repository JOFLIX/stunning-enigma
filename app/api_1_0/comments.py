# -*- coding:utf-8 -*-
from flask import jsonify, request, url_for, g
from . import api
from ..models import Post, User, Comment, Permission
from .decorators import permission_required
from app import db

# All comments
@api.route('/comments')
def get_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.paginate(page=page, per_page=10, error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_comments', page=page + 1, _external=True)
    return jsonify({
        'posts': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })

# Specific comment
@api.route('/comments/<int:id>')
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())

# All comments for an article
@api.route('/posts/<int:id>/comments')
def get_post_comments(id):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(page=page, per_page=10, error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_post_comments', id=id, page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_post_comments', id=id, page=page + 1, _external=True)
    return jsonify({
        'posts': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })

# Post a comment on an article
@api.route('/posts/<int:id>/comments', methods=['POST'])
@permission_required(Permission.COMMENT)
def new_comment(id):
    comment = Comment.from_json(request.json)
    post = Post.query.get_or_404(id)
    comment.post = post
    comment.author = g.current_user
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json()), 201, {'Location': url_for('api.get_comment', id=comment.id, _external=True)}
