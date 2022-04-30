from http import HTTPStatus

from application.errors import *
from application import *
from flask import jsonify


#   Useful routines
def cls():
    os.system("cls")


def clear():
    os.system("clear")


def drop_db(name: str = DFL_DATABASE_NAME):
    db.connection.drop_database(name)


def drop_collections(db_name: str = DFL_DATABASE_NAME, names: list[str] = None):
    dbase = db.connection[db_name]
    for name in names:
        dbase[name].drop()


app = create_app()


@app.errorhandler(Exception)
def return_exception(ex: Exception):
    print(ex)
    msgs = [str(arg) for arg in ex.args]
    resp = make_error(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        msg=f"Unhandled exception '{type(ex).__name__}'.",
        err_type='InternalFailure', errors=msgs,
    )
    return resp


@app.shell_context_processor
def make_shell_context():
    return {
        # generals
        'system': os.system, 'cls': cls, 'clear': clear,
        'db': db, 'drop_db': drop_db, 'drop_coll': drop_collections,

        # classes
        'User': User, 'Workspace': Workspace,
        'Context': UserWorkspaceResourceContext,
        'DataType': DataType, 'Benchmark': MongoBenchmark,
        'MetricSet': MongoStandardMetricSet,
        'Model': MongoModel,
    }


if __name__ == '__main__':
    print('DataType:\n', DataType.get_all_typenames(), '\n')
    app.run('0.0.0.0')