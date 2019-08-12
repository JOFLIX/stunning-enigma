# -*- coding:utf-8 -*-
from selenium import webdriver
import unittest
from app import create_app, db
from app.models import User, Role, Post
import threading
import time

class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        # Launch browser
        try:
            cls.client = webdriver.Safari()
        except:
            pass
        if cls.client:
            print 'nfjdjakkasfmaf'
            # Create program
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # Disable logging, keep the output brief
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # Create a database, simulate data padding
            db.create_all()
            Role.insert_roles()
            User.generate_fake(count=10)
            Post.generate_fake(count=10)

            # Add administrator
            role_admin = Role.query.filter_by(permissions=0xff).first()
            admin = User(email='zs@example.com',
                         username='zs',
                         password='111',
                         itsrole=role_admin,
                         confirmed=True)
            db.session.add(admin)
            db.session.commit()

            # Start the Flask server in one thread
            # threading.Thread(target=cls.app.run).start()
            threading.Thread.__init__(target=cls.app.run).start()
            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # The first one closes the Flask server and the second closes the browser.(Client)
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.close()

            db.drop_all()
            db.session.remove()
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    def test_admin_home_page(self):
        pass
