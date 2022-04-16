from application import *
from mongoengine import NotUniqueError
from flask import jsonify


#   Useful routines
def cls():
    os.system("cls")


def clear():
    os.system("clear")


app = create_app()


@app.errorhandler(Exception)
def return_exception(ex: Exception):
    print(ex)
    msgs = [str(arg) for arg in ex.args]
    resp = jsonify({
        'error': msgs,
    })
    resp.status_code = 500
    return resp


dummy_data = {
    "name": "DummyTwo",
    "description": "An example of dummy.",
    "type": "Dummy",
    "build": {
        "name": "DummyGen",
        "x": 9,
        "y": "stringa",
        "z": True,
    }
}

superdummy_data = {
    "name": "SuperDummyOne",
    "description": "An example of super dummy.",
    "type": "SuperDummy",
    "build": {
        "name": "SuperDummyGen",
        "bname": "SuperDummyOne",
        "desc": "...",
        "dummy": "DummyOne",
    }
}


@app.shell_context_processor
def make_shell_context():
    return {
        # generals
        'system': os.system, 'cls': cls, 'clear': clear,
        'db': db, 'data': dummy_data, 'super_data': superdummy_data,

        # classes
        'User': User, 'DataType': DataType,
        'Context': DictUserWorkspaceResourceContext,
        'NotUniqueError': NotUniqueError,
    }


if __name__ == '__main__':
    # print('DataType:\n', DataType.get_all_typenames(), '\n')
    app.run('0.0.0.0')