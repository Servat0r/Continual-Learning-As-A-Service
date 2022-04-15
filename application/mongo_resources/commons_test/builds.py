from __future__ import annotations
from application.mongo_resources.commons_test.datatypes import *


@MongoBuildConfig.register_build_config('DummyGen')
class DummyGenBuildConfig(MongoBuildConfig):

    x = db.IntField(required=True)
    y = db.StringField(required=True)
    z = db.BooleanField(required=True)

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Dummy')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        required = ['x', 'y', 'z']
        if not all(fname in data for fname in required):
            raise ValueError()
        x = data['x']
        y = data['y']
        z = data['z']
        result = isinstance(x, int) and isinstance(y, str) and isinstance(z, bool)
        return result, None if result else "Missing one or more parameter(s)."

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        if not cls.validate_input(data, tp, context):
            raise ValueError()
        x = data['x']
        y = data['y']
        z = data['z']
        # noinspection PyArgumentList
        return cls(x=x, y=y, z=z)

    def build(self, context: ResourceContext):
        tp = self.target_type()
        # noinspection PyArgumentList
        return tp(x=self.x, y=self.y, z=self.z)

    def update(self, data, context: ResourceContext):
        pass

    def delete(self, context: ResourceContext):
        pass


@MongoBuildConfig.register_build_config('SuperDummyGen')
class SuperDummyGenBuildConfig(MongoBuildConfig):

    __DUMMY_TYPE__ = t.cast(ReferrableDataType, DataType.get_type('Dummy')).config_type()

    bname = db.StringField(required=True)
    desc = db.StringField(required=True)
    dummy = db.ReferenceField(__DUMMY_TYPE__, required=True)

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('SuperDummy')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        required = ['bname', 'dummy']
        if not all(fname in data for fname in required):
            return False, f"Missing one or more parameters from {required}."
        else:
            return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        if not cls.validate_input(data, tp, context):
            raise ValueError()
        bname = data['bname']
        desc = data.get('desc') or ''
        dummy_name = data['dummy']
        dummy_uri = cls.__DUMMY_TYPE__.dfl_uri_builder(context, dummy_name)
        dummy = cls.__DUMMY_TYPE__.get_by_uri(dummy_uri)
        if dummy is None:
            raise ValueError()
        else:
            # noinspection PyArgumentList
            return cls(bname=bname, desc=desc, dummy=dummy)

    def build(self, context: ResourceContext):
        tp = self.target_type()
        dummy = self.dummy.build(context)
        # noinspection PyArgumentList
        return tp(name=self.bname, desc=self.desc, dummy=dummy)

    def update(self, data, context: ResourceContext):
        pass

    def delete(self, context: ResourceContext):
        pass