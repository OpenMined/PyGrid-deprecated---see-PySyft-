import os
#basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # ...
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #    'sqlite:///' + os.path.join(basedir, 'app.db')


    POSTGRES = {
	'user': 'postgres',
	'pw': 'password',
	'db': 'grid_example_dev',
	'host': 'localhost',
	'port': '5432',
    }
    SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:\%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES

    SQLALCHEMY_TRACK_MODIFICATIONS = False
