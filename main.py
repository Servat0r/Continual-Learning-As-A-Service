import os
from http import HTTPStatus
from torchvision.models import alexnet
from flask import url_for
from application import *


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
    msgs = [str(arg) for arg in ex.args]
    resp = make_error(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        msg=f"Unhandled exception '{type(ex).__name__}'.",
        err_type='InternalFailure', errors=msgs,
    )
    return resp


def user_n(n: int) -> t.Callable:
    def nth_user():
        return User.create(f"user{n}", f"user{n}@example.com", "1234@abcD")
    return nth_user


def wspace_n(n: int) -> t.Callable:
    def nth_wspace():
        return Workspace.create(f"wspace{n}", f"user{n}")
    return nth_wspace


def drop_exit():
    drop_db()
    exit()


@app.shell_context_processor
def make_shell_context():
    return {
        # generals
        'system': os.system, 'cls': cls, 'clear': clear, 'db': db,
        'drop_db': drop_db, 'drop_coll': drop_collections, 'drop_exit': drop_exit,

        # users & workspaces
        'User': User.user_class(), 'Workspace': Workspace.get_class(),
        'Context': UserWorkspaceResourceContext,

        # data managing
        'DataRepo': BaseDataRepository.get_class(),
        'DataManager': BaseDataManager,

        # datasets
        'Dataset': FileBasedClassificationDataset,

        # resources
        'DataType': DataType, 'Benchmark': MongoBenchmark,
        'Criterion': MongoCLCriterion, 'MetricSet': MongoStandardMetricSet,
        'Model': MongoModel, 'Optimizer': MongoCLOptimizer,
        'Strategy': MongoStrategy, 'Experiment': MongoCLExperiment,

        # helpers
        'user_n': user_n, 'wspace_n': wspace_n, 'model': alexnet(pretrained=True),
        'url_for': url_for,
        # 'user': user_n(1)(), 'wspace': wspace_n(1)(),

    }


if __name__ == '__main__':
    debug = bool(get_env('DEBUG', 0, int))
    if debug:
        app.logger.info(f"Current working directory: {os.getcwd()}")
    app.run('0.0.0.0')