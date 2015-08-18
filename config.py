import os

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLES = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

class ProductionConfig(Config):
    DEBUG = False

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

if __name__ == '__main__':
    print('{0}: {1}'.format('APP_SETTINGS', os.environ['APP_SETTINGS']))
    print('{0}: {1}'.format('DATABASE_URL', os.environ['DATABASE_URL']))
