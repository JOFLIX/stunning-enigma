# -*- coding:utf-8 -*-
import unittest
from app import create_app, db
from app.models import User, Role
from flask import url_for
import re

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # Test homepage
    def test_home_page(self):
        response = self.client.get(url_for('main.index'))    # The response obtained is index.html
        self.assertTrue(u'Log in first, please' in response.get_data(as_text=True))

    # Test registration and login
    def test_register_and_login(self):
        # Register new user
        response = self.client.post(url_for('auth.register'), data={
            'email': 'zs@example.com',
            'username': 'zs',
            'password': 'aa',
            'password2': 'aa'
        })
        self.assertTrue(response.status_code == 302)

        # Log in with a registered new user
        response = self.client.post(url_for('auth.login'), data={
            'email': 'zs@example.com',
            'password': 'aa'
        }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue(re.search(u'Hello,\s*zs', data))   # Regular expression matching
        self.assertTrue(u'You have not confirmed your account yet' in data)

        # Send confirmation token
        user = User.query.filter_by(email='zs@example.com').first()
        token = user.generate_confirm_token()
        response = self.client.get(url_for('auth.confirm', token=token),
                                   follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue(u'Thank you for your confirmation' in data)

        # sign out
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue(u'You have logged out' in response.data.decode('utf-8'))
