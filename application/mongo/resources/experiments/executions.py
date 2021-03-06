from __future__ import annotations

from application import TDesc, t
from application.database import db
from application.data_managing import BaseDataManager

from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.datatypes import BaseCLExperimentExecution, BaseCLExperiment


class MongoCLExperimentExecutionConfig(BaseCLExperimentExecution, db.EmbeddedDocument):

    experiment = db.ReferenceField('MongoCLExperimentConfig', required=True)
    exec_id = db.IntField(required=True)
    started = db.BooleanField(default=False)
    completed = db.BooleanField(default=False)

    start_time = db.DateTimeField(default=None)
    end_time = db.DateTimeField(default=None)

    status_code = db.IntField(default=200)
    payload = db.DictField(default=None)

    def base_dir(self):
        return self.experiment.base_dir() + [str(self.exec_id)]

    def get_logging_path(self):
        return self.experiment.get_logging_path(self.exec_id)

    def get_exec_id(self) -> int:
        return self.exec_id

    def get_csv_results(self) -> tuple[bool, t.Optional[TDesc]]:
        manager = BaseDataManager.get()
        if self.completed:
            train_csv = manager.read_from_file(('train_results.csv', self.get_logging_path(), -1), binary=False)
            eval_csv = manager.read_from_file(('eval_results.csv', self.get_logging_path(), -1), binary=False)
            if train_csv is None or eval_csv is None:
                return True, None
            else:
                return True, {
                    'train': train_csv,
                    'eval': eval_csv,
                }
        else:
            return False, None

    def get_final_model(self, descriptor=False):
        manager = BaseDataManager.get()
        if descriptor:
            fd = manager.get_file_pointer('model.pt', self.base_dir())
            return fd
        else:
            model = manager.read_from_file(('model.pt', self.base_dir(), -1))
            return model

    def to_dict(self) -> TDesc:
        return {
            'experiment': self.experiment.get_name(),
            'exec_id': self.exec_id,
            'claas_urn': self.claas_urn,
            'started': self.started,
            'completed': self.completed,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'results': {
                'status': self.status_code,
                'payload': self.payload,
            }
        }

    @property
    def claas_urn(self):
        return self.claas_urn_separator().join([self.experiment.claas_urn, str(self.exec_id)])

    @classmethod
    def get_by_claas_urn(cls, urn: str):
        components = urn.split(cls.claas_urn_separator())
        if len(components) < 2:
            raise ValueError("Invalid urn format!")
        exec_id = components[-1]
        exp_claas_urn_components = components[:-1]
        exp_claas_urn = cls.claas_urn_separator().join(exp_claas_urn_components)
        experiment = BaseCLExperiment.config_type().get_by_claas_urn(exp_claas_urn)
        return experiment.get_execution(int(exec_id))

    @classmethod
    def dfl_claas_urn_builder(cls, context: UserWorkspaceResourceContext, name: str, exec_id: int) -> str:
        exp_claas_urn = BaseCLExperiment.dfl_claas_urn_builder(context, name)
        return cls.claas_urn_separator().join([exp_claas_urn, str(exec_id)])


__all__ = [
    'MongoCLExperimentExecutionConfig',
]