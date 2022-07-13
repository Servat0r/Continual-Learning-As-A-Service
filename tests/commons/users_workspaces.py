"""
Testing on base users and workspaces operations.
"""
from __future__ import annotations
import unittest
from client import *

from tests.utils import *


class UserWorkspaceOpsTestCase(BaseTestCase):

    # Test parameters
    username = 'user-workspace-username'
    email = 'user_workspace_test_' + EMAIL
    password = PASSWORD
    workspace = 'user_workspace_workspace'
    host = HOST
    port = PORT
    client = BaseClient(host, port)
    deleted = False

    # "Macros"
    def register_login(self):
        # register
        self.assertBaseHandler(
            self.client.register(self.username, self.email, self.password), success_codes=HTTPStatus.CREATED,
        )

        # login
        self.assertBaseHandler(self.client.login(self.username, self.password))

    def create_workspace(self):
        # create workspace
        self.assertBaseHandler(self.client.create_workspace(self.workspace), success_codes=HTTPStatus.CREATED)

    def close_and_delete_workspace(self):
        # close workspace
        self.assertBaseHandler(self.client.close_workspace())

        # delete workspace
        self.assertBaseHandler(self.client.delete_workspace())

    def delete_user(self):
        # delete user
        self.assertBaseHandler(self.client.delete_user())
        self.deleted = True

    # Main test
    def test_main(self):
        self.deleted = False
        with self.client.session(self.username, self.workspace):
            try:
                # register and login
                self.register_login()

                # get_user
                self.assertBaseHandler(self.client.get_user())

                # edit_user
                self.assertBaseHandler(self.client.edit_user(self.username, "new_" + self.email))

                # create workspace
                self.create_workspace()

                # get workspace
                self.assertBaseHandler(self.client.get_workspace())

                # close and delete workspace
                self.close_and_delete_workspace()

                # logout
                self.assertBaseHandler(self.client.logout(exit_session=False))

                # login again
                self.assertBaseHandler(self.client.login(self.username, self.password))

                self.delete_user()
            finally:
                if not self.deleted:
                    # delete user data anyway
                    self.client.close_workspace(self.workspace)
                    self.client.delete_workspace(self.workspace)
                    self.client.delete_user()
                    self.deleted = True


if __name__ == '__main__':
    unittest.main()


__all__ = ['UserWorkspaceOpsTestCase']
