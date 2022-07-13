"""
Testing on base data repositories operations.
"""
from __future__ import annotations
import os
import unittest
from client import *

from tests.utils import *


class DataRepositoryOpsTest(BaseTestCase):

    # Test parameters
    username = 'data-repositories-username'
    email = 'data_repositories_test_' + EMAIL
    password = PASSWORD
    workspace = 'data_repositories_workspace'
    host = HOST
    port = PORT
    client = BaseClient(host, port)
    files_source_folder = os.path.abspath(os.path.join('..', '..', 'source_datasets'))

    repository_name = 'data_repository'
    repository_desc = 'Description of the repository.'
    mnist_root = 'mnist'
    mnist_train_folder = 'train'
    mnist_test_folder = 'test'
    mnist_train_subfolder = '0'

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

    def test_main(self):
        print(f"files_source_folder = {self.files_source_folder}")
        self.deleted = False
        with self.client.session(self.username, self.workspace):
            try:
                # register and login
                self.register_login()

                # create workspace
                self.create_workspace()

                self.assertBaseHandler(
                    self.client.create_data_repository(self.repository_name, self.repository_desc),
                    success_codes=HTTPStatus.CREATED,
                )

                self.assertBaseHandler(self.client.get_data_repository(self.repository_name))

                self.assertBaseHandler(self.client.get_data_repository_desc(self.repository_name))

                # Add and move directories
                # Create a 'mnist' directory, then add 'train' and 'first' as subdirectories and 'test' as subdirectory
                # of 'train', then move 'test' out of 'train' and 'first' inside of 'train'.
                self.assertBaseHandler(
                    self.client.create_subdir(self.repository_name, self.mnist_root),
                    success_codes=HTTPStatus.CREATED,
                )

                self.assertBaseHandler(
                    self.client.create_subdir(self.repository_name, self.mnist_train_folder, [self.mnist_root]),
                    success_codes=HTTPStatus.CREATED,
                )

                self.assertBaseHandler(
                    self.client.create_subdir(self.repository_name, self.mnist_train_subfolder, [self.mnist_root]),
                    success_codes=HTTPStatus.CREATED,
                )

                self.assertBaseHandler(
                    self.client.create_subdir(self.repository_name, self.mnist_test_folder,
                                              [self.mnist_root, self.mnist_train_folder]),
                    success_codes=HTTPStatus.CREATED,
                )

                self.assertBaseHandler(
                    self.client.move_subdir(
                        self.repository_name,
                        '/'.join([self.mnist_root, self.mnist_train_folder, self.mnist_test_folder]),
                        '/'.join([self.mnist_root, self.mnist_test_folder]),
                    )
                )

                self.assertBaseHandler(
                    self.client.move_subdir(
                        self.repository_name,
                        '/'.join([self.mnist_root, self.mnist_train_subfolder]),
                        '/'.join([self.mnist_root, self.mnist_train_folder, self.mnist_train_subfolder]),
                    )
                )

                self.assertBaseHandler(self.client.get_data_repository(self.repository_name))

                # Files sending (plain)
                # In the first iteration, files are added into an already existing directory ('0')
                # In the second one, a new directory would be created by the server ('1')
                for i in range(2):
                    basedir = os.path.join(self.files_source_folder, 'mnist_stub', 'train', str(i))
                    files = os.listdir(basedir)
                    files_and_labels = [(os.path.join(basedir, file), f'train/first/{file}', i) for file in files]
                    self.assertBaseHandler(
                        self.client.send_files(self.repository_name, files_and_labels, base_path=['mnist'])
                    )

                self.assertBaseHandler(self.client.get_data_repository(self.repository_name))

                # delete directory (ENTIRE train directory)
                self.assertBaseHandler(
                    self.client.delete_subdir(self.repository_name, '/'.join([self.mnist_root, self.mnist_train_folder]))
                )

                # Files sending (compressed)
                train_base_dir = ['mnist_stub', 'train']
                files_train_dict: list[tuple[str, str, int]] = []
                for i in range(2):
                    basedir = os.path.join(self.files_source_folder, *train_base_dir, str(i))
                    fnames = os.listdir(basedir)
                    for fname in fnames:
                        files_train_dict.append((os.path.join(basedir, fname), '/'.join([str(i), fname]), i))
                self.assertBaseHandler(self.client.send_files(
                    self.repository_name, files_train_dict, train_base_dir, files_mode='zip', zip_file_name='train.zip',
                ))

                # delete repository
                self.assertBaseHandler(self.client.delete_data_repository(self.repository_name))
                # close and delete workspace
                self.close_and_delete_workspace()
                # delete user
                self.delete_user()
            finally:
                if not self.deleted:
                    self.client.close_workspace(self.workspace)
                    self.client.delete_workspace(self.workspace)
                    self.client.delete_user()
                    self.deleted = True


if __name__ == '__main__':
    unittest.main()


__all__ = ['DataRepositoryOpsTest']