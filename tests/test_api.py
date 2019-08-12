# -*- coding:utf-8 -*-
import unittest
from app import create_app, db
from app.models import User, Role
from base64 import b64encode
from flask import url_for, json

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_api_headers(self, username, password):
        return {
            'Authorization': 'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_no_auth(self):
        response = self.client.get(url_for('api.get_posts'),
                                   content_type='application/json')
        self.assertTrue(response.status_code == 200)

    def test_posts(self):
        # Add a user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)     # Role is not empty
        u = User(email='zs@example.com', password='111', confirmed=True,
                 itsrole=r)
        db.session.add(u)
        db.session.commit()

        # Write an article
        response = self.client.post(url_for('api.new_post'),
                                    headers=self.get_api_headers('zs@example.com', '111'),
                                    data=json.dumps({'title': 'blog',
                                                     'body': 'body of the blog'}))
        self.assertTrue(response.status_code == 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # Get the article just released, the returned data is packaged by jsonify
        response = self.client.get(url, headers=self.get_api_headers('zs@example.com', '111'))
        response_json = json.loads(response.data.decode('utf-8'))
        self.assertTrue(response.status_code == 200)
        self.assertTrue(response_json['url'] == url)
        self.assertTrue(response_json['title'] == 'blog')
