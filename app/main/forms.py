from flask_wtf import FlaskForm
from wtforms import StringField,TextAreaField,SubmitField,SelectField
from wtforms.validators import Required,Email,EqualTo
from ..models import Subscriber
from wtforms import ValidationError


class PostForm(FlaskForm):
    title = StringField("Post Title",validators=[Required()])
    post = TextAreaField("Write your post here")
    category = SelectField("Post Category",choices=[('Tech','Tech'),('Travel','Travel'),('Fashion','Fashion'),('Food','Food'),('Life','Life'),('Culture','Culture')],validators=[Required()])
    submit = SubmitField('Submit')

class SubscriberForm(FlaskForm):
    email = StringField("Email Address",validators=[Required(),Email()])
    submit = SubmitField("Subscribe")

    def validate_email(self,data_field):
        if Subscriber.query.filter_by(email =data_field.data).first():
            raise ValidationError("Account already subscribed with that email")

class CommentForm(FlaskForm):
    comment = TextAreaField("Leave a Comment")
    submit = SubmitField('Submit')