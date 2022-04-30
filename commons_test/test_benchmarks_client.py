from sys import argv
import requests

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


if __name__ == '__main__':

    _SEP_ = '################################################'

    _COLLS_ = {'u', 'w', 'b', 'm'}
    # options
    _UW_ONLY_ = '--only_[[u][w][b][m]]'     # only operate on users (u), workspaces (w), benchmarks (b), metricsets (m)
    _NO_DEL_ = '--nodel_[[u][w][b][m]]'     # do not delete users (u), workspaces (w), benchmarks (b), metricsets (m)

    __only__ = set()
    __nodel__ = set()
    _only_set = False

    if len(argv) > 1:
        for i in range(1, len(argv)):
            if argv[i].startswith('--only_'):
                _only_set = True
                onlies = argv[i].split('--only_')[-1]
                for opt in onlies:
                    for c in _COLLS_:
                        if opt == c:
                            __only__.add(c)
                            break
            elif argv[i].startswith('--nodel_'):
                nodels = argv[i].split('--nodel_')[-1]
                for j in range(len(nodels)):
                    opt = nodels[j]
                    print(opt)
                    for c in _COLLS_:
                        if opt == c:
                            __nodel__.add(c)
                            break
            else:
                raise ValueError("Provide a correct cmdline argument!")

    if not _only_set:
        __only__ = __only__.union(_COLLS_)

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

    if 'u' in __only__:
        # register and login
        print_response(cl.register(username, email, password))
        print_response(cl.login(username, password))

        # user operations
        print_response(cl.get_user(username))
        print_response(cl.edit_user(username, new_email))
        print_response(cl.edit_password(password, new_password))

    if 'w' in __only__:
        # create and get workspaces
        print_response(cl.create_workspace('wspace1'))
        print_response(cl.get_workspace('wspace1'))

    if 'b' in __only__:
        # create and build benchmarks
        print_response(cl.create_benchmark(benchmark_name, benchmark_build, benchmark_desc))
        print_response(cl.build_benchmark(benchmark_name))

    if 'm' in __only__:
        # create and build metricsets
        print_response(cl.create_metric_set(metricset_name, metricset_build, metricset_desc))
        print_response(cl.build_metric_set(metricset_name))

    # create and build models
    print_response(cl.create_model(model_name, model_build, model_desc))
    print_response(cl.build_model(model_name))

    # delete models
    print_response(cl.delete_model(model_name))

    if 'm' not in __nodel__:
        # delete metricsets
        print_response(cl.delete_metric_set(metricset_name))

    if 'b' not in __nodel__:
        # delete benchmarks
        print_response(cl.delete_benchmark(benchmark_name))

    if 'w' not in __nodel__:
        # workspace close and deletions
        print_response(cl.close_workspace('wspace1'))
        print_response(cl.delete_workspace('wspace1'))

    if 'u' not in __nodel__:
        print_response(cl.delete_user())

    print("Done!")