# -*- coding:utf-8 -*-
from flask import render_template, flash, abort, redirect, url_for, request, current_app, make_response
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required
from ..models import Permission, User, Role, Post, Comment
from . import main
from .forms import EditProfileForm, EditProfileAdministratorForm, PostForm, CommentForm
from .. import db
from flask_sqlalchemy import get_debug_queries


@main.route('/', methods=['GET','POST'])
def index():
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed'))   # Determine if the cookie is greater than 0
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    page = request.args.get('page',1, type=int)       # 1 means that if not specified, the first page is rendered by default, and if it is 2, it defaults to the second page.
    pagination = query.order_by(Post.timestamp.desc()).paginate(
                                    page, per_page=10,
                                    error_out=False)  # Error_out=True page number out of range returns 404 error, False returns empty list
    posts = pagination.items
    return render_template('index.html', show_followed=show_followed,
                           posts=posts, pagination=pagination)

@main.route('/all')
@login_required
def show_all():
    response = make_response(redirect(url_for('main.index')))
    response.set_cookie('show_followed','',max_age=30*24*60*60)    # Judging whether the click is all or followed by the value of the cookie
    return response

@main.route('/followed')
@login_required
def show_followed():
    response = make_response(redirect(url_for('main.index')))
    response.set_cookie('show_followed','2',max_age=30*24*60*60)
    return response

# Homepage article fixed link routing, plus comment form
@main.route('/post/<int:id>', methods=['GET','POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object(),
                          )
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('main.post', id=post.id, page=-1))    # Come to the last page of the comment
    page = request.args.get('page',1,type=int)
    if page == -1:
        page = (post.comments.count()-1)/10 + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
                    page, per_page=10, error_out=False
                    )
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)

@main.route('/blog',methods=['GET','POST'])
@login_required
def blog():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post = Post(title=form.title.data,body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('blog.html',form=form)


@main.route('/admin')      # Only the administrator is allowed to enter in the login state, otherwise it will be 403 to prohibit the login interface.
@login_required
@admin_required
def for_admin_only():
    return u'Manager entering'

@main.route('/moderator')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def for_moderator_only():
    return u'Manager entering'

@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)

# Focus on users
@main.route('/follow/<username>')
def follow(username):
    u = User.query.filter_by(username=username).first()
    if u is None:
        flash(u'No such user')
        return redirect(url_for('main.index'))
    if current_user.is_following(u):
        flash(u'Has already paid attention to this user')
        return redirect(url_for('main.user', username=username))
    current_user.follow(u)
    flash(u'Concerned %s' % username)
    return redirect(url_for('main.user', username=username))

# unsubscribe
@main.route('/unfollow/<username>')
def unfollow(username):
    u = User.query.filter_by(username=username).first()
    if u is None:
        flash(u'No such user')
        return redirect(url_for('main.index'))
    if u.is_followed_by(current_user):
        current_user.unfollow(u)
        flash(u'Cancel %s s concern' % username)
        return redirect(url_for('main.user', username=username))

# List all fans
@main.route('/followers/<username>')
def followers(username):
    u = User.query.filter_by(username=username).first()
    page = request.args.get('page', 1, type=int)
    pagination = u.followers.paginate(page, per_page=10, error_out=False)
    follows = [{'user':item.follower,'timestamp':item.timestamp}
               for item in pagination.items]                      # Convert to a dictionary list
    return render_template('followers.html', title=u'Fans',user=u, pagination=pagination, follows=follows)

# List all my concerns
@main.route('/followed-by/<username>')
def followed_by(username):
    u = User.query.filter_by(username=username).first()
    page = request.args.get('page', 1, type=int)
    pagination = u.followed.paginate(page, per_page=10, error_out=False)
    follows = [{'user':item.followed,'timestamp':item.timestamp}
               for item in pagination.items]                      # Convert to a dictionary list
    return render_template('followers.html', title=u's concern',user=u, pagination=pagination, follows=follows)


# Ordinary user level editing
@main.route('/edit-profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        flash(u'Your personal information has been changed')
        db.session.add(current_user)              # update personal information
        db.session.commit()
        return redirect(url_for('main.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',form=form)

# Administrator level editor
@main.route('/edit-profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)  # Find this user
    form = EditProfileAdministratorForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.itsrole = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash(u"The user's information has been updated")
        return redirect(url_for('main.user',username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id          # Role_id is associated with its role
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html',form=form,user=user)

# Role_id is associated with its role
@main.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTRATOR):       # The current author is not the person who published the blog and is not the administrator
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.post',id=post.id))
    form = PostForm()
    form.title.data = post.title
    form.body.data = post.body
    return render_template('edit_post.html', form=form)

# Coordinator management review, all comments
@main.route('/moderate', methods=['GET','POST'])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page',1,type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
                                        page, per_page=10, error_out=False)
    comments = pagination.items
    return render_template('moderate.html',
                           comments=comments, pagination=pagination, page=page)

# Prohibit this comment
@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.moderate',page=request.args.get('page',1,type=int)))

# Enable this comment
@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.moderate', page=request.args.get('page', 1, type=int)))

@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server,shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return '-----Shutting down------'

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response
