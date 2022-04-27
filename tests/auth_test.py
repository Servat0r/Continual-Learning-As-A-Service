import unittest
from dotenv import load_dotenv
from application import *
from client import *


def handle_response(response, target_status_code=HTTPStatus.OK):
    print(response.status_code, response.reason, response.json(), sep='\n')
    assert(response.status_code == target_status_code)


load_dotenv('test.env')


class MongoTestConfig(MongoConfig):
    TESTING = True
    MONGODB_DB = os.environ.get('MONGODB_DATABASE') or 'test'

    TEST_HOST = os.environ.get('HOST') or '192.168.1.120'
    TEST_PORT = int(os.environ.get('PORT') or '5000')

    TEST_USERNAME = os.environ.get('USERNAME') or 'user1'
    TEST_NEW_USERNAME = os.environ.get('NEW_USERNAME') or 'new_user_1'

    TEST_EMAIL = os.environ.get('EMAIL') or 'abc@example.com'
    TEST_NEW_EMAIL = os.environ.get('NEW_EMAIL') or 'def@example.com'

    TEST_PASSWORD = os.environ.get('PASSWORD') or '1234?abcD'
    TEST_NEW_PASSWORD = os.environ.get('NEW_PASSWORD') or '4321@Abcd'

    TEST_WORKSPACE = os.environ.get('WORKSPACE') or 'wspace1'


class MyTestCase(unittest.TestCase):

    __DFL_DBNAME__ = MongoTestConfig.MONGODB_DB
    __INIT_COLLS__ = ['users', 'workspaces']

    __HOST__ = MongoTestConfig.TEST_HOST
    __PORT__ = MongoTestConfig.TEST_PORT

    __USERNAME__ = MongoTestConfig.TEST_USERNAME
    __NEW_USERNAME__ = MongoTestConfig.TEST_NEW_USERNAME
    __EMAIL__ = MongoTestConfig.TEST_EMAIL
    __NEW_EMAIL__ = MongoTestConfig.TEST_NEW_EMAIL
    __PASSWORD__ = MongoTestConfig.TEST_PASSWORD
    __NEW_PASSWORD__ = MongoTestConfig.TEST_NEW_PASSWORD

    __WORKSPACE__ = MongoTestConfig.TEST_WORKSPACE

    def get_db(self):
        return self.db.connection[self.dbname]

    def init_db(self, cnames: t.Sequence[str] = None):
        dbase = self.get_db()
        if cnames is not None:
            for cname in cnames:
                coll = dbase[cname]
                coll.insert_one({}, bypass_document_validation=True)
                coll.delete_one({})

    def drop_db(self):
        mongo_client = self.db.connection
        mongo_client.drop_database(self.dbname)

    def setUp(self) -> None:
        self.db = db
        self.app = create_app(MongoTestConfig)
        self.dbname = self.app.config['MONGODB_DB']

        self.host = self.__HOST__
        self.port = self.__PORT__

        self.init_db(cnames=self.__INIT_COLLS__)
        self.client = BaseClient(self.host, self.port)

    def tearDown(self) -> None:
        self.drop_db()
        print('Test finished')

    def test_init_db(self):
        dbase = self.get_db()
        colls = list(dbase.list_collections())
        assert(len(colls) == 2)

    def test_users(self):
        handle_response(
            self.client.register(self.__USERNAME__, self.__EMAIL__, self.__PASSWORD__), HTTPStatus.CREATED
        )
        handle_response(self.client.login(self.__USERNAME__, self.__PASSWORD__))
        handle_response(self.client.get_user(self.__USERNAME__))
        handle_response(self.client.edit_user(self.__USERNAME__, self.__NEW_EMAIL__))
        handle_response(self.client.edit_password(self.__PASSWORD__, self.__NEW_PASSWORD__))
        handle_response(self.client.delete_user())
        print("Done!")


if __name__ == '__main__':
    unittest.main(verbosity=2)