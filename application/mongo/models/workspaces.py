from __future__ import annotations

from application.resources import *
from application.validation import *
from application.database import db
from application.data_managing import BaseDataRepository
from application.mongo.base import *
from application.data_managing import BaseDataManager


class WorkspaceMetadata(MongoBaseMetadata):
    pass


@Workspace.set_class
class MongoWorkspace(MongoBaseWorkspace):

    # 1. Fields
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'

    meta = {
        'indexes': [
            {'fields': ('owner', 'name'), 'unique': True}
        ]
    }

    owner = db.ReferenceField(MongoBaseUser, required=True)
    name = db.StringField(max_length=WORKSPACE_EXPERIMENT_MAX_CHARS, required=True)
    status = db.StringField(max_length=8, required=True)
    metadata = db.EmbeddedDocumentField(WorkspaceMetadata, required=True)

    # 2. Uri methods
    @classmethod
    def get_by_uri(cls, uri: str):
        """
        uri is of the form "workspace::<username>::<wname>"
        :param uri:
        :return:
        """
        s = uri.split(cls.uri_separator())
        print(s)
        user = t.cast(MongoBaseUser, User.canonicalize(s[1]))
        workspace = s[2]
        ls = cls.get(owner=user, name=workspace)
        return ls[0] if len(ls) > 0 else None

    @property
    def uri(self):
        context = UserWorkspaceResourceContext(self.owner.get_name(), self.name)
        return self.dfl_uri_builder(context)

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
               open_on_create: bool = True, parent_locked=False) -> MongoBaseWorkspace | None:

        owner = t.cast(MongoBaseUser, User.canonicalize(owner))

        if owner is None:
            return None

        result, msg = validate_workspace_experiment(name)
        if not result:
            raise ValueError(msg)

        with owner.sub_resource_create(locked=parent_locked):

            now = datetime.utcnow()
            # noinspection PyArgumentList
            workspace = cls(
                name=name,
                status=Workspace.OPEN if open_on_create else Workspace.CLOSED,
                owner=owner,
                metadata=WorkspaceMetadata(created=now, last_modified=now),
            )
            if workspace is not None:
                with workspace.resource_create():
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
    def delete(self, locked=False, parent_locked=False):
        with self.get_owner().sub_resource_delete(locked=parent_locked):
            with self.resource_delete(locked=locked):
                if self.is_open():
                    self.close()
                try:
                    for experiment in (self.all_experiments() or []):
                        print(experiment)
                        experiment.delete(parent_locked=True)
                    for repository in self.data_repositories():
                        print(repository)
                        repository.delete(parent_locked=True)
                except Exception as ex:
                    return False, ex

                try:
                    db.Document.delete(self)
                    return True, None
                except Exception as ex:
                    return False, ex

    # 6. Read/Update Instance methods
    def __repr__(self):
        return f"Workspace <{self.name}> [uri = {self.uri}]"

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

    def save(self, create=False):
        db.Document.save(self, force_insert=create)

    def update_last_modified(self, time: datetime = None, save: bool = True):
        self.metadata.update_last_modified(time)
        if save:
            self.save()

    def to_dict(self) -> TDesc:
        return {
            'name': self.name,
            'status': self.status,
            'owner': self.owner.to_dict(),
            'metadata': self.metadata.to_dict(),
        }

    # 7. Query-like methods
    def data_repositories(self):    # TODO!
        return list(BaseDataRepository.get(self))

    def all_experiments(self):
        return NotImplemented

    def running_experiments(self):
        return NotImplemented

    # 8. Status methods
    def open(self, save: bool = True):
        self.status = Workspace.OPEN
        self.update_last_modified(save=save)

    def close(self, save: bool = True):
        self.status = Workspace.CLOSED
        self.update_last_modified(save=save)

    def is_open(self):
        return self.status == Workspace.OPEN