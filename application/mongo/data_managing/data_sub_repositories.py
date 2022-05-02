from __future__ import annotations
from datetime import datetime

from application.database import *
from application.resources import TBoolExc, TDesc
from application.models import Workspace
from application.data_managing import BaseDataRepository, BaseDataSubRepository
from application.mongo.mongo_base_metadata import MongoBaseMetadata


class MongoDataSubRepositoryMetadata(MongoBaseMetadata):
    pass


@BaseDataSubRepository.set_class
class MongoDataSubRepository(BaseDataSubRepository, db.Document):

    # 1. Fields
    meta = {
        'indexes': [
            {'fields': ('name', 'data_repository'), 'unique': True}
        ]
    }

    data_repository = db.ReferenceField(BaseDataRepository.get_class())
    name = db.StringField(required=True)
    root = db.StringField(required=True)
    metadata = db.EmbeddedDocumentField(MongoDataSubRepositoryMetadata)
    # TODO files = db.ListField(db.EmbeddedDocumentField('MongoDatasetFile'))

    # 2. Uri methods
    @classmethod
    def get_by_uri(cls, uri: str):
        s = uri.split(cls.uri_separator())
        username = s[1]
        workspace = s[2]
        repository = s[3]
        name = s[4]
        repository = BaseDataRepository.canonicalize((username, workspace), repository)
        return MongoDataSubRepository.objects(name=name, data_repository=repository).first()

    @property
    def uri(self):
        return type(self).dfl_uri_builder(self)

    # 3. General classmethods
    @classmethod
    def get_by_data_repository(cls, repository: BaseDataRepository) -> list[BaseDataSubRepository]:
        return list(cls.objects(data_repository=repository).all())

    # 4. Create + callbacks
    @classmethod
    def before_create(cls, name: str, repository: BaseDataRepository) -> TBoolExc:
        return True, None

    @classmethod
    def after_create(cls, subrepo: BaseDataSubRepository) -> TBoolExc:
        subrepo.root = f"DataSubRepository_{subrepo.get_id()}"
        subrepo.save()
        manager = Workspace.get_data_manager()
        repository = subrepo.get_data_repo()
        owner = repository.get_owner()
        workspace = repository.get_workspace()
        return manager.create_subdir(
            subrepo.get_root(),
            parents=[
                owner.user_base_dir(),
                workspace.workspace_base_dir(),
                repository.get_root(),
            ]
        )

    @classmethod
    def create(cls, name: str, repository: BaseDataRepository, root: str = None,
               save: bool = True) -> BaseDataSubRepository | None:
        # TODO Validation!
        now = datetime.utcnow()
        if root is None:
            root = f"DataSubRepository_{name}"
        # noinspection PyArgumentList
        subrepo = cls(
            data_repository=repository,
            name=name,
            root=root,
            metadata=MongoDataSubRepositoryMetadata(created=now, last_modified=now),
        )
        if save:
            subrepo.save(create=True)
            print(f"Created DataRepository '{name}' with id '{subrepo.id}'.")
        return subrepo

    # 5. Delete + callbacks
    @classmethod
    def before_delete(cls, subrepo: BaseDataSubRepository) -> TBoolExc:
        try:
            # TODO Aggiungere chiusura etc.
            return True, None
        except Exception as ex:
            return False, ex

    @classmethod
    def after_delete(cls, subrepo: BaseDataSubRepository) -> TBoolExc:
        try:
            repository = subrepo.get_data_repo()
            manager = Workspace.get_data_manager()
            workspace = repository.get_workspace()
            owner = repository.get_owner()
            parents = [
                owner.user_base_dir(),
                workspace.workspace_base_dir(),
                repository.get_root(),
            ]
            return manager.remove_subdir(
                subrepo.get_root(),
                parents=parents,
            )
        except Exception as ex:
            return False, ex

    @classmethod
    def delete(cls, subrepo: BaseDataSubRepository) -> TBoolExc:
        pass

    # 6. Read/Update Instance methods
    def get_id(self):
        return self.id

    def get_root(self) -> str:
        return self.root

    def get_data_repo(self) -> BaseDataRepository:
        return self.data_repository

    def get_name(self) -> str:
        return self.name

    def get_all_metadata(self) -> TDesc:
        return self.metadata.to_dict()

    def save(self, create=False):
        db.Document.save(self, force_insert=create)

    def to_dict(self) -> TDesc:
        return {
            'name': self.name,
            'root': self.root,
            'data_repository': self.data_repository.to_dict(),
            # TODO 'files': [f.to_dict() for f in self.files],
            'metadata': self.metadata.to_dict(),
        }

    # 7. Query-like instance methods
    def get_files(self):
        return NotImplemented

    def get_file(self, name: str):
        return NotImplemented

    # 8. Status methods

    # 9. Special methods