import requests

from client import *


if __name__ == '__main__':

    _SEP_ = '################################################àà'

    def print_response(response):
        print(response.status_code, response.reason, response.json(), _SEP_, sep='\n')

    cl = BaseClient("192.168.1.120")
    print(cl.__dict__)
    username = 'servator'
    email = 'abc@example.com'
    password = '1234?abcD'
    new_email = 'def@example.com'
    new_password = '4321?abcD'
    print_response(cl.register(username, email, password))
    print_response(cl.login(username, password))
    print_response(cl.get_user(username))
    print_response(cl.edit_user(username, new_email))
    print_response(cl.edit_password(password, new_password))
    print_response(cl.create_workspace('wspace1'))
    print_response(cl.get_workspace('wspace1'))
    print_response(cl.close_workspace('wspace1'))
    print_response(cl.delete_workspace('wspace1'))
    print_response(cl.delete_user())
    print("Done!")