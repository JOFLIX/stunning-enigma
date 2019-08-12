# -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo

#Login form
class LoginForm(FlaskForm):
    email = StringField(label=u'mailbox',validators=[DataRequired(), Length(1,64), Email()], id='loginlength')
    password = PasswordField(label=u'password',validators=[DataRequired()], id='loginlength')
    remember_me = BooleanField(label=u'remember me', id='loginlength')
    submit = SubmitField(label=u'Login')

#Registry
class RegisterForm(FlaskForm):
    email = StringField(label=u'email address',validators=[DataRequired(), Length(1,64), Email()], id='registerlength')
    username = StringField(label=u'username',validators=[DataRequired(), Length(1,64)],
                           id='registerlength')
    password = PasswordField(label=u'password',validators=[DataRequired(),
                            EqualTo('password2', message=u'Password must be the same')], id='registerlength')
    password2 = PasswordField(label=u'confirm password',validators=[DataRequired()], id='registerlength')
    submit = SubmitField(label=u'Register now')
