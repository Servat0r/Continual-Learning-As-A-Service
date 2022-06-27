from .auth import *
from .users import *
from .workspaces import *
from .data_repositories import *
from .resources import *

from .benchmarks import *
from .metricsets import *
from .models import *
from .criterions import *
from .optimizers import *
from .strategies import *

from .experiments import *
from .predictions import *

blueprints = {
    auth_bp,
    users_bp,
    workspaces_bp,
    data_repositories_bp,

    benchmarks_bp,
    metricsets_bp,
    models_bp,
    criterions_bp,
    optimizers_bp,
    strategies_bp,

    experiments_bp,
    predictions_bp,
}