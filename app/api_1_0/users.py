# -*- coding:utf-8 -*-
from flask import jsonify, request, url_for, g
from . import api
from ..models import Post, User


# Query all users
@api.route('/users')
def get_users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.paginate(page=page, per_page=10, error_out=False)
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_users', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_users', page=page+1, _external=True)
    users = pagination.items
    return jsonify({
        'users': [user.to_json() for user in users],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })

# Query a specific user
@api.route('/users/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())

# Query all blog posts of a user
@api.route('/users/<int:id>/posts')
def get_user_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(page=page, per_page=10, error_out=False)
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_posts', id=id, page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_posts', id=id, page=page + 1, _external=True)
    posts = pagination.items
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })

# Query all the followers of a user's blog
@api.route('/users/<int:id>/timeline')
def get_followers_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts.order_by(Post.timestamp.desc()).paginate(page=page, per_page=10, error_out=False)
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_posts', id=id, page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_posts', id=id, page=page + 1, _external=True)
    posts = pagination.items
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })
