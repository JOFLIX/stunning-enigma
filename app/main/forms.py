# -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length
from flask_pagedown.fields import PageDownField
from ..models import Role

# Home blog post form
class PostForm(FlaskForm):
    title = StringField(label=u'Blog title', validators=[DataRequired()], id='titlecode')
    body = PageDownField(label=u'Blog content', validators=[DataRequired()])
    submit = SubmitField(label=u'submit')

class CommentForm(FlaskForm):
    body = PageDownField(label=u'Comment', validators=[DataRequired()])
    submit = SubmitField(label=u'submit')


# Normal user login form
class EditProfileForm(FlaskForm):
    name = StringField(label=u'actual name', validators=[Length(0,64)])
    location = StringField(label=u'address', validators=[Length(0,64)])
    about_me = TextAreaField(label=u'about me')
    submit = SubmitField(label=u'submit')


# Administrator login form, which can edit user's email, username, confirmation status and role
class EditProfileAdministratorForm(FlaskForm):
    email = StringField(label=u'mailbox', validators=[DataRequired(), Length(1,64), Email()])
    username = StringField(label=u'username', validators=[DataRequired(), Length(1, 64)])
    confirmed = BooleanField(label=u'confirm')
    role = SelectField(label=u'Corner character', coerce=int)

    name = StringField(label=u'actual name', validators=[Length(0, 64)])
    location = StringField(label=u'address', validators=[Length(0, 64)])
    about_me = TextAreaField(label=u'about me')
    submit = SubmitField(label=u'submit')

    # To initialize the check box of role when initializing
    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdministratorForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name)]
        self.user = user
