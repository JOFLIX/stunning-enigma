# -*- coding:utf-8 -*-
from . import db, login_manager
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from datetime import datetime
import hashlib
from markdown import markdown
import bleach

class Permission:
    FOLLOW = 0x01             # Focus on users
    COMMENT = 0x02            # Comment in someone else's article
    WRITE_ARTICLES = 0x04     # write an essay
    MODERATE_COMMENTS = 0x08  # Manage comments by others
    ADMINISTRATOR = 0xff      # Manager authority

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True, unique=True)
    default = db.Column(db.Boolean, default=False)      # Only one role's field should be set to True, others are False
    permissions = db.Column(db.Integer)                 # Different roles have different permissions
    users = db.relationship('User', backref='itsrole')  # The Role object references users, and the User object references itsrole
                                                        # Is an invisible property, one-to-many
    @staticmethod
    def insert_roles():
        roles = {
            'User':(Permission.FOLLOW|Permission.COMMENT|
                     Permission.WRITE_ARTICLES, True),     # Only the default user's default is True.
            'Moderare':(Permission.FOLLOW|Permission.COMMENT|
                    Permission.WRITE_ARTICLES|Permission.MODERATE_COMMENTS, False),
            'Administrator':(0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)     # Represents the follower, corresponding to the follower of the relationship
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)     # Represents the person being followed, corresponding to the followed of the relationship
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=True)
    password = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True, unique=True)     # Create a new mailbox field
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String, nullable=True)          # Add a password hash value to the model
    confirmed = db.Column(db.Boolean, default=False)             # Whether the mailbox token is clicked
    name = db.Column(db.String(64))         # Nickname in user information
    location = db.Column(db.String(64))     # User address
    about_me = db.Column(db.Text())         # User introduction
    member_since = db.Column(db.DateTime, default=datetime.utcnow)             # Registration time
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)               # Last visit time
    posts = db.relationship('Post', backref='author', lazy='dynamic',
                            cascade='all, delete-orphan')            # A user has multiple publications, one-to-many
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],      # The user is following other users, and for other users, the user is its follower(Followers)
                               backref=db.backref('follower', lazy='joined'),    # Corresponding to follower_id
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id],     # The followers of the user, for the followers, the followers pay attention to the user
                                backref=db.backref('followed', lazy='joined'),   # Corresponding to followed_id
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def to_json(self):
        user_json = {
            'url': url_for('api.get_user', id=self.id, _external=True),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'post_count': self.posts.count()
        }
        return user_json


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)        # Initialize the parent class
        if self.itsrole is None:
            if self.email == current_app.config['FLASK_ADMIN']:                  # The mailbox is the same as the administrator's mailbox
                self.itsrole = Role.query.filter_by(permissions=0xff).first()    # Authority for the manager
            else:
                self.itsrole = Role.query.filter_by(default=True).first()       # Default user

    def follow(self, user):                          # Pay attention to user
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)     #Self is the follower, the follower_id corresponds to it, while self.followed (self pays attention to other users) adds a new value
            db.session.add(f)                            # User is the follower, followed_id corresponds to it, while user.followers (user is followed by other users) to add a new value
            db.session.commit()

    def unfollow(self, user):                        # Cancel the attention of user
        f = self.followed.filter_by(followed_id=user.id).first()       # Find the user with the following_id=user.id from other users that the user is following.
        if f is not None:
            db.session.delete(f)
            db.session.commit()

    def is_following(self, user):                    # Do you care about this user?
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):                  # Whether it is followed by user
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):                       # List all articles that the user is following
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
                    .filter(Follow.follower_id == self.id)


    def can(self, permissions):          # Check user permissions
        return self.itsrole is not None and \
               (self.itsrole.permissions & permissions) == permissions

    def is_administrator(self):         # Check if it is a manager
        return self.can(Permission.ADMINISTRATOR)

    def ping(self):
        self.last_seen = datetime.utcnow()         # Refresh last access time
        db.session.add(self)
        db.session.commit()

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&r={rating}&d={default}'.format(url=url, hash=hash,
                                                            size=size, rating=rating,
                                                            default=default)

    @property             # Trying to read the value of password, returning an error, because password is no longer recoverable
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter      # When setting the value of the password property, the assignment function will call the generate_password_hash function.
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirm_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'confirm': self.id})               # Return a token

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)           # Update the confirmed field to the database, but have not submitted it yet
        db.session.commit()
        return True

    # Generate virtual users
    @staticmethod
    def generate_fake(count=10):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    @staticmethod                           # Pay attention to yourself
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def generate_auth_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])



class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod  # This is a static method because the client cannot specify the blog and author to which the comment belongs, only the server can be designated as the current user.
    def from_json(json_body):
        body = json_body.get('body')
        if body is None or body == '':
            print ('error')
        return Comment(body=body)

    def to_json(self):
        comment_json = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp
        }
        return comment_json

    @staticmethod
    def on_body_changed(target, value, oldvalue, initiator):
        allow_tags = ['a', 'abbr', 'acronym', 'b', 'code',
                      'em', 'strong']
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
                                                       tags=allow_tags, strip=True))

class AnonymousUser(AnonymousUserMixin):   # Anonymous User
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)                   # Rich text processing fields on the server
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    @staticmethod      # This is a static method because the client cannot specify the author of the article, only the server can be designated as the current user.
    def from_json(json_body):
        title = json_body.get('title')
        body = json_body.get('body')
        if body is None or body == '':
            print ('error')
        return Post(title=title, body=body)

    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id, _external=True),
            'title': self.title,
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'comment_count': self.comments.count()
        }
        return json_post

    @staticmethod
    def generate_fake(count=10):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            p = Post(title=forgery_py.lorem_ipsum.sentence(),
                     body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
                     timestamp=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()

    @staticmethod                # Add a title to all published blog posts
    def generate_title():
        from random import seed
        import forgery_py

        seed()
        posts = Post.query.all()
        for post in posts:
            if post.title is None:
                post.title = forgery_py.lorem_ipsum.sentence()
                db.session.add(post)
        db.session.commit()

    @staticmethod
    def on_body_changed(target, value, oldvalue, initiator):
        allow_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                      'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                      'h1', 'h2', 'h3', 'p', 'span', 'code', 'pre',
                      'img', 'hr', 'div']
        allow_attributes = ['src', 'alt', 'href', 'class']
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html',extensions=['markdown.extensions.extra','markdown.extensions.codehilite']),
                                                       tags=allow_tags, attributes=allow_attributes, strip=True))


@login_manager.user_loader      # Load the user's callback function, and get the current user after success.
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.anonymous_user = AnonymousUser   # Set it to the value of current_user when the user is not logged in.

db.event.listen(Post.body, 'set', Post.on_body_changed)
db.event.listen(Comment.body, 'set', Comment.on_body_changed)
