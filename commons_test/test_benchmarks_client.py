from sys import argv

from client import *

benchmark_name = "SplitMNISTOne"
benchmark_type = "Benchmark"
benchmark_desc = "An example of SplitMNIST benchmark."
benchmark_build = {
    "name": "SplitMNIST",
    "n_experiences": 5,
}

metricset_name = "AccuracyAndLossOne"
metricset_type = "StandardMetricSet"
metricset_desc = "..."
metricset_build = {
    'name': "StandardMetricSet",
    'accuracy': {
        'minibatch': True,
        'epoch': False,
        'experience': True,
        'stream': True,
    }
}

model_name = "SimpleMLPOne"
model_type = "Model"
model_desc = "..."
model_build = {
    'name': 'SimpleMLP',
    'num_classes': 10,
    'input_size': 28 * 28,
}

criterion_name = "CrossEntropyLossOne"
criterion_type = "CLCriterion"
criterion_desc = "..."
criterion_build = {
    'name': 'CrossEntropyLoss',
}

optimizer_name = 'SGDOne'
optimizer_desc = '...'
optimizer_build = {
    'name': 'SGD',
    'learning_rate': 0.001,
    'momentum': 0.9,
    'model': model_name,
}

strategy_name = 'NaiveOne'  # 'CumulativeOne'
strategy_desc = '...'
strategy_build = {
    'name': 'Naive',  # 'Cumulative',  # 'SynapticIntelligence',
    'model': model_name,
    'optimizer': optimizer_name,
    'criterion': criterion_name,
    'metricset': metricset_name,
    # 'si_lambda': [1.0],
    # 'eps': 0.001,
}

experiment_name = 'ExperimentOne'
experiment_desc = '...'
experiment_build = {
    'name': 'ExperimentBuild',
    'strategy': strategy_name,
    'benchmark': benchmark_name,
}


if __name__ == '__main__':

    _SEP_ = '################################################\n\n'

    __users__ = 'users'
    __workspaces__ = 'workspaces'
    __benchmarks__ = 'benchmarks'
    __metric_sets__ = 'metric_sets'
    __models__ = 'models'
    
    _COLLS_ = {
        __users__: 'u',
        __workspaces__: 'w',
        __benchmarks__: 'b',
        __metric_sets__: 'ms',
        __models__: 'm',
    }

    # options
    _UW_ONLY_ = '--only_'     # only operate on given collections (u,w,b,...)
    _NO_DEL_ = '--nodel_'     # do not delete given collections (u,w,b,...)

    __only__ = set()
    __nodel__ = set()
    _only_set = False

    if len(argv) > 1:
        for i in range(1, len(argv)):
            if argv[i].startswith(_UW_ONLY_):
                _only_set = True
                onlies = argv[i].split(_UW_ONLY_, 1)[1].split('_')
                for opt in onlies:
                    for c in _COLLS_:
                        if opt == c:
                            __only__.add(c)
                            break
            elif argv[i].startswith(_NO_DEL_):
                nodels = argv[i].split(_NO_DEL_, 1)[1].split('_')
                for j in range(len(nodels)):
                    opt = nodels[j]
                    print(opt)
                    for c in _COLLS_:
                        if opt == _COLLS_[c]:
                            __nodel__.add(c)
                            break
            else:
                raise ValueError("Provide a correct cmdline argument!")

    if not _only_set:
        __only__ = __only__.union(_COLLS_.keys())

    def print_response(response):
        print(response.status_code, response.reason, response.json(), _SEP_, sep='\n')

    print(f"__only__ = {__only__}", f"__nodel__ = {__nodel__}", sep='\n')

    BaseClient.set_debug()
    cl = BaseClient("192.168.1.120")
    username = 'servator'
    email = 'abc@example.com'
    password = '1234?abcD'
    new_email = 'def@example.com'
    new_password = '4321?abcD'

    if __users__ in __only__:
        # register and login
        print_response(cl.register(username, email, password))
        print_response(cl.login(username, password))

        # user operations
        print_response(cl.get_user(username))
        print_response(cl.edit_user(username, new_email))
        print_response(cl.edit_password(password, new_password))

    if __workspaces__ in __only__:
        # create and get workspaces
        print_response(cl.create_workspace('wspace1'))
        print_response(cl.get_workspace('wspace1'))

    if __benchmarks__ in __only__:
        # create and build benchmarks
        print_response(cl.create_benchmark(benchmark_name, benchmark_build, benchmark_desc))
        print_response(cl.build_benchmark(benchmark_name))
        print_response(cl.rename_benchmark(benchmark_name, f"New_{benchmark_name}"))
        print_response(
            cl.update_benchmark(
                f"New_{benchmark_name}", {
                    'name': benchmark_name,
                    'description': 'Description.',
                    'build': {
                        'n_experiences': 4,
                        'shuffle': False,
                    }
                }
            )
        )

    if __metric_sets__ in __only__:
        # create and build metricsets
        print_response(cl.create_metric_set(metricset_name, metricset_build, metricset_desc))
        print_response(cl.build_metric_set(metricset_name))

    if __models__ in __only__:
        # create and build models
        print_response(cl.create_model(model_name, model_build, model_desc))
        print_response(cl.build_model(model_name))

    # todo if ... __only__:
    print_response(cl.create_optimizer(optimizer_name, optimizer_build, optimizer_desc))
    print_response(cl.build_optimizer(optimizer_name))

    print_response(cl.create_criterion(criterion_name, criterion_build, criterion_desc))
    print_response(cl.build_criterion(criterion_name))

    print_response(cl.create_strategy(strategy_name, strategy_build, strategy_desc))
    print_response(cl.build_strategy(strategy_name))

    # todo experiments!

    if __models__ not in __nodel__:
        # delete models
        print_response(cl.delete_model(model_name))

    if __metric_sets__ not in __nodel__:
        # delete metricsets
        print_response(cl.delete_metric_set(metricset_name))

    if __benchmarks__ not in __nodel__:
        # delete benchmarks
        print_response(cl.delete_benchmark(benchmark_name))

    if __workspaces__ not in __nodel__:
        # workspace close and deletions
        print_response(cl.close_workspace('wspace1'))
        print_response(cl.delete_workspace('wspace1'))

    if __users__ not in __nodel__:
        print_response(cl.delete_user())

    print("Done!")