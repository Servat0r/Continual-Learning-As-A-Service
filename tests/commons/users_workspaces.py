from __future__ import annotations
import unittest
from client import *

from tests.utils import *



class UserWorkspaceOpsTestCase(BaseTestCase):

    username = 'user-workspace-username'
    email = EMAIL
    password = PASSWORD
    workspace = 'user_workspace_workspace'
    host = HOST
    port = PORT
    client = BaseClient(host, port)

    def test_user_workspace(self):
        with self.client.session(self.username, self.workspace):
            # register
            self.assertBaseHandler(
                self.client.register(self.username, self.email, self.password), success_codes=HTTPStatus.CREATED,
            )

            # login
            self.assertBaseHandler(self.client.login(self.username, self.password))

            # get_user
            self.assertBaseHandler(self.client.get_user())

            # edit_user
            self.assertBaseHandler(self.client.edit_user(self.username, "new_" + self.email))

            # create workspace
            self.assertBaseHandler(self.client.create_workspace(self.workspace), success_codes=HTTPStatus.CREATED)

            # get workspace
            self.assertBaseHandler(self.client.get_workspace())

            # close workspace
            self.assertBaseHandler(self.client.close_workspace())

            # delete workspace
            self.assertBaseHandler(self.client.delete_workspace())

            # logout
            self.assertBaseHandler(self.client.logout(exit_session=False))

            # login again
            self.assertBaseHandler(self.client.login(self.username, self.password))

            # delete user
            self.assertBaseHandler(self.client.delete_user())


if __name__ == '__main__':
    unittest.main()
