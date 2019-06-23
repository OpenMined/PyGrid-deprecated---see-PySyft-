import unittest
from grid.app import create_app, db
from grid.app.models import Worker, WorkerObject

class FlaskBaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
                'TESTING': True,
                'SQLALCHEMY_DATABASE_URI': "sqlite:///:memory:"
            })
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

