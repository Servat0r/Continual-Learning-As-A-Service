from __future__ import annotations

from time import sleep
from .base import *


class UserWorkspaceShellTestCase(BaseShellTest):

    username = 'user-workspace-shell-username'
    email = f"user_workspace_shell_{EMAIL}"
    wname = 'user_workspace_shell_workspace'

    deleted = False

    def test_main(self):
        self.deleted = False
        try:
            self.assertTrue(self.create_user_workspace())
            print(f"User = [{self.user}]")
            print(f"Workspace = [{self.workspace}]")
            sleep(10)
            self.assertTrue(self.delete_user_workspace())
            self.deleted = True
        finally:
            if not self.deleted:
                self.delete_user_workspace()
                self.deleted = True


if __name__ == '__main__':
    unittest.main(verbosity=2)