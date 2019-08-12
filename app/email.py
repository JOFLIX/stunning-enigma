# -*- coding:utf-8 -*-
from threading import Thread
from flask_mail import Message
from flask import render_template
from . import mail
from flask import current_app    # This way you don't have to use from manager import app
import os

def send_async_mail(app, msg):
    with app.app_context():
        mail.send(msg)


# The four parameters are (1. Receiver Email Address 2. Subject 3. Template 4. Variable Parameters)
def send_mail(to, subject, template, **kw):
    app = current_app._get_current_object()
    msg = Message(subject=subject, sender=app.config['FLASKY_MAIL_SENDER'],
                  recipients=[to])                               # Subject, sender (read from environment variable), recipient
    msg.body = render_template(template + '.txt', **kw)          # Text content
    msg.html = render_template(template + '.html', **kw)         # Text rendering
    thr = Thread(target=send_async_mail, args=[app, msg])
    thr.start()
    return thr
