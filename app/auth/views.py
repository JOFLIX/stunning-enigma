# -*- coding:utf-8 -*-
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user
from ..email import mail_message
# from ..email import send_mail
from . import auth
from .. import db
from ..models import User


@auth.route('/login', methods=['GET', 'POST'])
def login():
    from app.auth.forms import LoginForm
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):  # Password verification succeeded
            login_user(user, form.remember_me.data)
            return redirect(url_for('main.index'))
        flash(u'Incorrect account or password')
    return render_template('login.html', title=u'Login', form=form)

@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash(u'You have logged out')
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    from app.auth.forms import RegisterForm
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    password=form.password.data, email=form.email.data)  # Add a new user to the database
        db.session.add(user)
        db.session.commit()
        User.add_self_follows()           # Add yourself as your own concern
        token = user.generate_confirm_token()                            # Generate a token
        send_mail(user.email, u'Please confirm your account', 'confirm', user=user, token=token) # Send mail
        flash (u' has a message sent to your mailbox')
        return redirect(url_for('auth.login'))    # This step has been a problem, can not be redirected, jump directly to the following
    else:
        return render_template('register.html', title=u'Register', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))          # Repeated click on the token of the mailbox
    if current_user.confirm(token):
        flash(u'Thank you for your confirmation')
    else:
        flash(u'The link has expired or expired')
    return redirect(url_for('main.index'))

@auth.before_app_request          # The user has logged in, the user account has not been confirmed, and the requested endpoint is not in the auth authentication blueprint.
def before_request():
    if current_user.is_authenticated:
        current_user.ping()              # Refresh the last access time before each request
        if not current_user.confirmed \
            and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')      # If the current anonymous account is alive and confirmed, return to the home page directly, otherwise the display is not confirmed.
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('unconfirmed.html')

@auth.route('/resend_email')
@login_required
def resend_email():
    token = current_user.generate_confirm_token()
    send_mail(current_user.email, u'Confirm your account', 'confirm', user=current_user, token=token)
    flash(u'A new email has been sent to your email address')
    return redirect(url_for('main.index'))
