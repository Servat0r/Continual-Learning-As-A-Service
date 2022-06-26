from __future__ import annotations
from datetime import datetime

from application.utils import t, TBoolStr, TDesc
from application.validation import *
from application.database import db
from application.models import User, Workspace
from application.data_managing import BaseDataManager, BaseDataRepository

from application.resources import *

from application.mongo.locking import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.base import MongoBaseUser, MongoBaseWorkspace


class WorkspaceMetadata(MongoBaseMetadata):
    pass


@Workspace.set_class
class MongoWorkspace(MongoBaseWorkspace):

    # 1. Fields
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'

    _COLLECTION = 'workspaces'

    meta = {
        'collection': _COLLECTION,
        'indexes': [
            {'fields': ('owner', 'name'), 'unique': True}
        ]
    }

    owner = db.ReferenceField(MongoBaseUser, required=True)
    name = db.StringField(required=True)
    status = db.StringField(max_length=8, required=True)
    metadata = db.EmbeddedDocumentField(WorkspaceMetadata, required=True)

    @property
    def parents(self) -> set[RWLockableDocument]:
        return {self.owner}

    # 2. Uri methods
    @classmethod
    def get_by_claas_urn(cls, urn: str):
        """
        urn is of the form "workspace:<username>:<wname>"
        :param urn:
        :return:
        """
        s = urn.split(cls.claas_urn_separator())
        user = t.cast(MongoBaseUser, User.canonicalize(s[1]))
        workspace = s[2]
        ls = cls.get(owner=user, name=workspace)
        return ls[0] if len(ls) > 0 else None

    @property
    def claas_urn(self):
        context = UserWorkspaceResourceContext(self.owner.get_name(), self.name)
        return self.dfl_claas_urn_builder(context)

    # 3. General classmethods
    @classmethod
    def get(cls, owner: str | MongoBaseUser = None, name: str = None, **kwargs) -> t.Sequence[MongoBaseWorkspace]:
        if owner is not None:
            owner = User.canonicalize(owner)
            kwargs['owner'] = owner
        if name is not None:
            kwargs['name'] = name
        return list(cls.objects(**kwargs).all())

    @classmethod
    def get_by_owner(cls, owner: str | MongoBaseUser):
        owner = t.cast(MongoBaseUser, User.canonicalize(owner))
        return cls.get(owner=owner)

    @classmethod
    def all(cls):
        return cls.get()

    # 4. Create + callbacks
    @classmethod
    def create(cls, name: str, owner: str | MongoBaseUser, save: bool = True,
               open_on_create: bool = True, parents_locked=False) -> MongoBaseWorkspace | None:

        owner = t.cast(MongoBaseUser, User.canonicalize(owner))

        if owner is None:
            return None

        result, msg = validate_workspace_resource_experiment(name)
        if not result:
            raise ValueError(msg)

        with owner.sub_resource_create(locked=parents_locked):

            now = datetime.utcnow()
            # noinspection PyArgumentList
            workspace = cls(
                name=name,
                status=Workspace.OPEN if open_on_create else Workspace.CLOSED,
                owner=owner,
                metadata=WorkspaceMetadata(created=now, last_modified=now),
            )
            if workspace is not None:
                with workspace.resource_create(parents_locked=True):
                    if save:
                        workspace.save(create=True)
                        print(f"Created workspace '{workspace}' with id '{workspace.id}'.")
                    manager = BaseDataManager.get()
                    manager.create_subdir(
                        workspace.workspace_base_dir(),
                        parents=[workspace.get_owner().user_base_dir()]
                    )
                    manager.create_subdir(
                        workspace.data_base_dir(),
                        parents=workspace.data_base_dir_parents(),
                    )
                    manager.create_subdir(
                        workspace.experiments_base_dir(),
                        parents=workspace.experiments_base_dir_parents(),
                    )
            return workspace

    # 5. Delete + callbacks
    def delete(self, locked=False, parents_locked=False):

        with self.resource_delete(locked=locked, parents_locked=parents_locked):
            if self.is_open():
                self.close()
            try:
                ModelClass = t.cast(ReferrableDataType, DataType.get_type('Model')).config_type()
                MetricSetClass = t.cast(ReferrableDataType, DataType.get_type('StandardMetricSet')).config_type()
                CLOptimizerClass = t.cast(ReferrableDataType, DataType.get_type('CLOptimizer')).config_type()
                CLCriterionClass = t.cast(ReferrableDataType, DataType.get_type('CLCriterion')).config_type()
                BenchmarkClass = t.cast(ReferrableDataType, DataType.get_type('Benchmark')).config_type()

                cl_models = ModelClass.get(self.owner, self)
                msets = MetricSetClass.get(self.owner, self)
                optims = CLOptimizerClass.get(self.owner, self)
                crits = CLCriterionClass.get(self.owner, self)

                context = UserWorkspaceResourceContext(self.owner.get_name(), self.get_name())

                for repository in self.data_repositories():
                    # noinspection PyArgumentList
                    repository.delete(context, parents_locked=True)

                for model in cl_models:
                    model.delete(context, parents_locked=True)

                for mset in msets:
                    mset.delete(context, parents_locked=True)

                for optim in optims:
                    optim.delete(context, parents_locked=True)

                for crit in crits:
                    crit.delete(context, parents_locked=True)

                bmarks = BenchmarkClass.get(owner=self.owner, workspace=self)
                for bmark in bmarks:
                    bmark.delete(context, parents_locked=True)

                manager = BaseDataManager.get()
                manager.remove_subdir(
                    self.workspace_base_dir(),
                    parents=[self.get_owner().user_base_dir()]
                )
                db.Document.delete(self)
                return True, None
            except Exception as ex:
                return False, ex

    # 6. Read/Update Instance methods
    def __repr__(self):
        return f"Workspace <{self.name}> [urn = {self.claas_urn}]"

    def get_id(self):
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_owner(self) -> MongoBaseUser:
        return self.owner

    def workspace_base_dir(self) -> str:
        return f"Workspace_{self.get_id()}"

    def data_base_dir_parents(self) -> list[str]:
        return [self.get_owner().user_base_dir(), self.workspace_base_dir()]

    def experiments_base_dir_parents(self) -> list[str]:
        return [self.get_owner().user_base_dir(), self.workspace_base_dir()]

    def rename(self, old_name: str, new_name: str) -> TBoolStr:
        if not self.is_open():
            return False, f"Workspace '{self.name}' is closed!"
        elif self.name != old_name:
            return False, "Old names are not equals!"
        else:
            self.name = new_name
            try:
                self.save()
                self.update_last_modified()
                return True, None
            except Exception as ex:
                return False, ex.args[0]

    def save(self, create=False) -> bool:
        # noinspection PyBroadException
        # noinspection PyUnusedLocal
        try:
            if create:
                db.Document.save(self, force_insert=create)
            else:
                self.update_last_modified(save=False)
                db.Document.save(self, save_condition={'id': self.id})
            return True
        except Exception as ex:
            return False

    def update_last_modified(self, time: datetime = None, save: bool = True):
        self.metadata.update_last_modified(time)
        if save:
            self.save()

    def to_dict(self, links=True) -> TDesc:
        data = {
            'name': self.name,
            'status': self.status,
            'metadata': self.metadata.to_dict(),
        }
        if links:
            data['owner'] = self.owner.to_dict(links=False)
        else:
            data['owner'] = self.owner.get_name()
        return data

    # 7. Query-like methods
    def data_repositories(self):
        return list(BaseDataRepository.get(workspace=self))

    # 8. Status methods
    def open(self, save: bool = True):
        self.status = Workspace.OPEN
        self.update_last_modified(save=save)

    def close(self, save: bool = True):
        self.status = Workspace.CLOSED
        self.update_last_modified(save=save)

    def is_open(self):
        return self.status == Workspace.OPEN


__all__ = [
    'WorkspaceMetadata',
    'MongoWorkspace',
]