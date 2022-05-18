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
            'uri': self.uri,
            'started': self.started,
            'completed': self.completed,
            'results': {
                'status': self.status_code,
                'payload': self.payload,
            }
        }

    @property
    def uri(self):
        return self.uri_separator().join([self.experiment.uri, str(self.exec_id)])

    @classmethod
    def get_by_uri(cls, uri: str):
        components = uri.split(cls.uri_separator())
        if len(components) < 2:
            raise ValueError("Invalid uri format!")
        exec_id = components[-1]
        exp_uri_components = components[:-1]
        exp_uri = cls.uri_separator().join(exp_uri_components)
        experiment = BaseCLExperiment.config_type().get_by_uri(exp_uri)
        return experiment.get_execution(int(exec_id))

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext, name: str, exec_id: int) -> str:
        exp_uri = BaseCLExperiment.dfl_uri_builder(context, name)
        return cls.uri_separator().join([exp_uri, str(exec_id)])


__all__ = [
    'MongoCLExperimentExecutionConfig',
]