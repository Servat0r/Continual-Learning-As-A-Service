from __future__ import annotations
from time import sleep

from avalanche.benchmarks import GenericCLScenario
from avalanche.training.strategies import BaseStrategy

from application.utils import TDesc
from application.resources.datatypes import BaseCLExperiment, BaseCLExperimentRunConfig


@BaseCLExperimentRunConfig.register_default_run_config()
class StdTrainTestRunConfig(BaseCLExperimentRunConfig):

    @classmethod
    def run(cls, experiment: BaseCLExperiment) -> bool:
        cl_scenario: GenericCLScenario = experiment.get_benchmark().get_value()
        cl_strategy: BaseStrategy = experiment.get_strategy().get_value()

        train_stream = cl_scenario.train_stream
        test_stream = cl_scenario.test_stream

        results: list[TDesc] = []
        for experience in train_stream:
            cl_strategy.train(experience)
            results.append(cl_strategy.eval(test_stream))

        print(*results, sep='\n')   # TODO Replace with results registering!
        return True