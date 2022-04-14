from application import *


#   Useful routines
def cls():
    os.system("cls")


def clear():
    os.system("clear")


app = create_app()


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
        'User': User, 'MongoDummy': MongoDummy, 'MongoSuperDummy': MongoSuperDummy,
        'DataType': DataType, 'Context': DictUserWorkspaceResourceContext,
        'MongoDummyDoc': MongoDummyDocument, 'MongoSuperDummyDoc': MongoSuperDummyDocument,
    }


if __name__ == '__main__':
    # print('DBResource:\n', DBResource.get_all_resource_types(), '\n')
    print('DataType:\n', DataType.get_all_typenames(), '\n')
    app.run()