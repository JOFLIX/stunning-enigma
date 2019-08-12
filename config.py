# -*- coding:utf-8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SSL_DISABLE = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    MAIL_SERVER = 'smtp.163.com'           # Configure the smtp service of the 163 mailbox, first you need to open the smtp service for your mailbox.
    MAIL_PORT = 465                       # The port is 465
    MAIL_USE_SSL = True                   # TLS service failed, use SSL
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASK_ADMIN = os.environ.get('FLASK_ADMIN')
    FLASKY_MAIL_SENDER = os.environ.get('MAIL_USERNAME')
    POSTS_PER_PAGE = os.environ.get('POSTS_PER_PAGE')
    FLASKY_SLOW_DB_QUERY_TIME = 0.5

    @staticmethod
    def init_app(app):
        pass

# Test environment
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    WTF_CSRF_ENABLED = False

# Debugging the environment
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

# Production environment
class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')

class HerokuConfig(ProductionConfig):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)


conifg = {
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'heroku': HerokuConfig
}
