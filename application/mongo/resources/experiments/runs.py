from __future__ import annotations

import sys
import traceback
from torch.nn import Module

from avalanche.benchmarks import GenericCLScenario
from avalanche.training.templates import SupervisedTemplate

from application.utils import TDesc, TOptBoolAny
from application.data_managing import BaseDataManager
from application.resources.datatypes import BaseCLExperiment, BaseCLExperimentRunConfig


def _save_model(model: Module, model_directory: list[str] = None) -> TOptBoolAny:
    if model_directory is not None:
        manager = BaseDataManager.get()
        result, exc = manager.save_model(model, model_directory)
        if not result:
            print(exc)
            traceback.print_exception(*sys.exc_info())
            return False, exc
    return True, None


@BaseCLExperimentRunConfig.register_default_run_config()
@BaseCLExperimentRunConfig.register_run_config('FixedTestSet')
class StdTrainTestRunConfig(BaseCLExperimentRunConfig):

    @classmethod
    def run(cls, experiment: BaseCLExperiment, model_directory: list[str] = None) -> TOptBoolAny:
        try:
            cl_scenario: GenericCLScenario = experiment.get_benchmark().get_value()
            cl_strategy: SupervisedTemplate = experiment.get_strategy().get_value()

            # noinspection PyUnresolvedReferences
            train_stream = cl_scenario.train_stream
            # noinspection PyUnresolvedReferences
            test_stream = cl_scenario.test_stream

            print(f"Using {cl_strategy.__class__.__name__} strategy ...")
            results: list[TDesc] = []
            for experience in train_stream:
                cl_strategy.train(experience)
                results.append(cl_strategy.eval(test_stream))

            model_saved, exc = _save_model(cl_strategy.model, model_directory)
            return model_saved, results if model_saved else exc
        except Exception as ex:
            traceback.print_exception(*sys.exc_info())
            return False, ex


@BaseCLExperimentRunConfig.register_run_config('GrowingTestSet')
class GrowingTestSetRunConfig(BaseCLExperimentRunConfig):

    @classmethod
    def run(cls, experiment: BaseCLExperiment, model_directory: list[str] = None) -> TOptBoolAny:
        try:
            cl_scenario: GenericCLScenario = experiment.get_benchmark().get_value()
            cl_strategy: SupervisedTemplate = experiment.get_strategy().get_value()

            # noinspection PyUnresolvedReferences
            train_stream = cl_scenario.train_stream
            # noinspection PyUnresolvedReferences
            test_stream = cl_scenario.test_stream

            print(f"Using {cl_strategy.__class__.__name__} strategy ...")
            results: list[TDesc] = []
            i = 1
            for experience in train_stream:
                cl_strategy.train(experience)
                actual_test_stream = test_stream[:i]
                results.append(cl_strategy.eval(actual_test_stream))

            model_saved, exc = _save_model(cl_strategy.model, model_directory)
            return model_saved, results if model_saved else exc
        except Exception as ex:
            traceback.print_exception(*sys.exc_info())
            return False, ex


@BaseCLExperimentRunConfig.register_run_config('JointTraining')
class JointTrainingRunConfig(BaseCLExperimentRunConfig):

    @classmethod
    def run(cls, experiment: BaseCLExperiment, model_directory: list[str] = None) -> TOptBoolAny:
        try:
            cl_scenario: GenericCLScenario = experiment.get_benchmark().get_value()
            cl_strategy: SupervisedTemplate = experiment.get_strategy().get_value()

            # noinspection PyUnresolvedReferences
            train_stream = cl_scenario.train_stream
            # noinspection PyUnresolvedReferences
            test_stream = cl_scenario.test_stream

            print(f"Using {cl_strategy.__class__.__name__} strategy ...")
            results: list[TDesc] = []
            cl_strategy.train(train_stream)
            results.append(cl_strategy.eval(test_stream))

            if model_directory is not None:
                manager = BaseDataManager.get()
                result, exc = manager.save_model(cl_strategy.model, model_directory)
                if not result:
                    print(exc)
                    traceback.print_exception(*sys.exc_info())
                    return False, exc
            return True, results
        except Exception as ex:
            traceback.print_exception(*sys.exc_info())
            return False, ex


__all__ = [
    'StdTrainTestRunConfig',
    'GrowingTestSetRunConfig',
    'JointTrainingRunConfig',
]