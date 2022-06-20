"""
Base testcase(s) for verifying correct resource creation and building.
"""
from __future__ import annotations
import unittest
from application import *

from tests.utils import *


class BaseShellTest(BaseTestCase):

    username = 'shell_username'
    email = EMAIL
    password = PASSWORD
    wname = 'shell_workspace'
    app = None
    user = None
    workspace = None

    def setUp(self) -> None:
        super().setUp()
        self.app = create_app()
        self.app.app_context().push()

    def tearDown(self) -> None:
        self.app.app_context().pop()
        super().tearDown()

    def create_user_workspace(self) -> bool:
        try:
            self.user = User.create(self.username, self.email, self.password)
            self.workspace = Workspace.create(self.wname, self.username)
            return True
        except Exception as ex:
            print(ex)
            return False

    def delete_user_workspace(self) -> bool:
        try:
            self.workspace.close()
            self.workspace.delete()
            self.workspace = None
            self.assertTrue(self.delete_user())
            return True
        except Exception as ex:
            print(ex)
            return False

    def delete_user(self) -> bool:
        try:
            self.user.delete()
            self.user = None
            return True
        except Exception as ex:
            print(ex)
            return False


if __name__ == '__main__':
    unittest.main(verbosity=2)


__all__ = ['BaseShellTest']