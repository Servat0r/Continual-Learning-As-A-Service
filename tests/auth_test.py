import unittest
import pymongo.collection
from config import *
from resources import *
from application import *
import requests


class MongoTestConfig(MongoConfig):
    TESTING = True
    MONGODB_DB = 'test'


class MyTestCase(unittest.TestCase):

    __INIT_COLLS__ = ['users', 'workspaces']
    __base_url__ = 'http://127.0.0.1:5000'

    __username_0__ = 'user1'
    __username_1__ = 'user2'

    __email_0__ = 'user1@example.com'
    __email_1__ = 'user2@example.com'

    def user_url(self, username: str = None):
        base = f"{self.__base_url__}/users"
        if username is not None:
            return f"{base}/{username}"
        else:
            return base + "/"

    def wspace_url(self, username: str, wname: str = None):
        assert(username is not None)
        base = f"{self.user_url(username)}/workspaces"
        if wname is not None:
            return f"{base}/{wname}"
        else:
            return base + "/"

    def init_db(self, dbname: str = None, cnames: t.Sequence[str] = None):
        client = self.db.connection
        dbase = client[dbname]
        if cnames is not None:
            for cname in cnames:
                coll: pymongo.collection.Collection = dbase[cname]
                coll.insert_one({}, bypass_document_validation=True)
                coll.delete_one({})

    def register(self, username: str, email: str, password: str):
        return requests.post(
            self.user_url(), json={
                "username": username,
                "email": email,
                "password": password,
            }
        )

    # TODO Completare!

    def setUp(self) -> None:
        self.db = db
        self.app = create_app(MongoTestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.init_db(dbname='test', cnames=self.__INIT_COLLS__)

    def tearDown(self) -> None:
        client = self.db.connection
        client.drop_database('test')

    def test_init_db(self):
        client = db.connection
        dbase = client['test']
        colls = list(dbase.list_collections())
        print(colls)
        assert(len(colls) == 2)

    def test_user_workspace_operations(self):
        pass

    def test_populate(self):
        user1 = User.create('user1')
        assert(User.objects.count() == 1)
        wspace1 = Workspace.create('wspace1', 'user1')
        assert(Workspace.objects.count() == 1)
        assert(wspace1.owner == user1)
        assert(Workspace.get_by_owner(user1)[0] == wspace1)


if __name__ == '__main__':
    unittest.main(verbosity=2)