# Base datatypes.
from __future__ import annotations
from resources.utils import *
from resources.contexts import *


class DataType:

    __datatypes: dict[str, t.Type[DataType]] = {}

    # TODO REMOVE!
    @classmethod
    def is_primitive(cls) -> bool:
        return issubclass(cls, Primitive)

    # TODO REMOVE!
    @classmethod
    def is_generator(cls) -> bool:
        return issubclass(cls, Generator)

    @classmethod
    def default_typename(cls) -> str:
        """
        Default typename (name of the class).
        :return:
        """
        return cls.__name__

    @classmethod
    def canonical_typename(cls) -> str:
        """
        "Super" typename (name of a common 'interface' for overwriting default one).
        :return:
        """
        return cls.__name__

    @staticmethod
    def canonicalize(resource_type: str | t.Type[ReferrableDataType]) -> TBoolStr:
        """
        Canonization for parameters passed as resource_type.
        :param resource_type:
        :return:
        """
        if isinstance(resource_type, str):
            return True, resource_type
        elif issubclass(resource_type, ReferrableDataType):
            return True, resource_type.canonical_typename()
        else:
            return False, None

    @classmethod
    def type_aliases(cls) -> set[str]:
        result = {cls.default_typename(), cls.canonical_typename()}
        for item in DataType.__datatypes.items():
            if item[1] == cls:
                result.add(item[0])
        return result

    @staticmethod
    def get_all_typenames() -> dict[str, t.Type[DataType]]:
        return DataType.__datatypes.copy()

    @staticmethod
    def set_resource_type(aliases: list[str] | None = None, canonical_typename: bool = True):
        def setter(cls: t.Type[DataType]):
            nonlocal aliases, canonical_typename
            if aliases is None:
                aliases = set()
            else:
                aliases = set(aliases)
            aliases.add(cls.default_typename())
            for name in aliases:
                DataType.__datatypes[name] = cls
            if canonical_typename:
                DataType.__datatypes[cls.canonical_typename()] = cls
            return cls
        return setter

    @staticmethod
    def get_type(name: str) -> t.Type[DataType] | None:
        return DataType.__datatypes.get(name)

    @staticmethod
    def get_generator_type(name: str) -> t.Type[Generator] | None:
        dt = DataType.get_type(name)
        if issubclass(dt, Generator):
            return dt
        else:
            return None

    @classmethod
    @abstractmethod
    def validate_data(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        pass

    @classmethod
    def build_from_data(cls, name: str, context: ResourceContext) -> DataType:
        pass


class WrapperDataType(DataType, ABC):

    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def set_value(self, new_value):
        self.value = new_value


class Generator(DataType):
    """
    Base class for generators.
    """

    def __repr__(self):
        return f"Generator<{self.target_type()}>[name = {self.name}, formal_parameters = " \
                f"{type(self).formal_parameters()}]"

    @property
    def name(self):
        return type(self).canonical_typename()

    @classmethod
    @abstractmethod
    def formal_parameters(cls) -> set[Parameter]:
        pass

    @classmethod
    def required_parameters(cls) -> set[Parameter]:
        f = filter(lambda param: param.required, cls.formal_parameters())
        return set(f)

    @classmethod
    def actual_parameters(cls, instance_data: t.Optional[TDesc] = None) -> set[Parameter]:
        params = cls.formal_parameters()
        if instance_data is None:
            return params
        else:
            contained = set()
            keys = list(instance_data.keys())
            for param in params:
                if param.name in keys:
                    contained.add(param)
            return contained

    @staticmethod
    @abstractmethod
    def target_type() -> t.Type[ReferrableDataType]:
        pass

    @classmethod
    def check_required(cls, instance_data: TDesc) -> tuple[bool, set[Parameter] | None]:
        keys = set(instance_data.keys())
        required_names = map(lambda param: param.name, cls.required_parameters())
        required_names = set(required_names)
        missing = required_names.difference(keys)
        if len(missing) > 0:
            return False, missing
        else:
            return True, None

    @classmethod
    def validate_data(cls, obj: t.Any, context: ResourceContext) -> TBoolStr:
        """
        {
            "name": <name>,
            "parameters": {
                ...
            }
        }
        :param obj:
        :param context:
        :return:
        """
        if isinstance(obj, cls):
            return True, None
        elif not isinstance(obj, dict):
            return False, "Incorrect object."
        else:
            check = all(name in obj for name in ['name', 'parameters'])
            if not check:
                raise SyntaxError('Missing paramater(s).')
            else:
                gen_name = obj.get('name')
                gen_params = obj.get('parameters')
                if DataType.get_type(gen_name) != cls:
                    raise ValueError('Incorrect generator!')
                else:
                    ok, missing = cls.check_required(gen_params)
                    if not ok:
                        return False, f"Missing parameters: {missing}."
                    for param_def in cls.actual_parameters(gen_params):
                        param_value = gen_params[param_def.name]
                        result, msg = param_def.validate(param_value, context)
                        if not result:
                            return False, msg
                    return True, None


class ReferrableDataType(DataType, URIBasedResource):

    """
    "Interface-mixin" for referrable resources that rely on external storage.
    """
    @classmethod
    def get_generator(cls, data: TDesc) -> str | None:
        gen = data.get('generator')
        if gen is not None:
            return gen.get('name')
        else:
            return None

    @staticmethod
    @abstractmethod
    def config_type():
        pass

    @abstractmethod
    def set_metadata(self, **kwargs):
        pass

    @abstractmethod
    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        pass

    @classmethod
    def validate_data(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        """
        "Wrapper" validation method.
        :param data:
        :param context:
        :return:
        """
        cfg_type = cls.config_type()
        return cfg_type.validate_input(data, context)

    @classmethod
    def build_from_data(cls, name: str, context: ResourceContext) -> ReferrableDataType:
        cfg_type = cls.config_type()
        uri = cfg_type.dfl_uri_builder(context, name)
        resource_config = cfg_type.get_by_uri(uri)
        return resource_config.build(context) if resource_config is not None else None


class Parameter(JSONSerializable):

    def __init__(self, name: str, td: t.Type[DataType], description: str, required: bool):
        self.name = name
        self._type = td
        self.description = description
        self.required = required

    def __repr__(self):
        return f"Parameter<{self._type.canonical_typename()}>[name = {self.name}, required = {self.required}] "

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        check = all(name in data for name in ['name', 'type', 'description', 'required'])
        if not check:
            raise SyntaxError('Missing parameters')
        else:
            name = data.get('name')
            description = data.get('description')
            required = data.get('required')
            typename = data.get('type')
            check = all(isinstance(field, str) for field in [name, typename, description]) \
                and isinstance(required, bool)
            if not check:
                raise TypeError('Some parameters were not of correct type.')
            td = DataType.get_type(typename)
            if td is None:
                raise ValueError(f"Unknown typename: '{typename}'.")
            return Parameter(name, td, description, required)

    def to_dict(self) -> TDesc:
        return {
            'name': self.name,
            'type': self._type.canonical_typename(),
            'description': self.description,
            'required': self.required,
        }

    def validate(self, obj: t.Any, context: ResourceContext) -> TBoolStr:
        return self._type.validate_data(obj, context)

    def build(self, obj: t.Any, context: ResourceContext) -> DataType:
        return self._type.build_from_data(obj, context)


class Primitive(WrapperDataType):
    """
    Primitive data types (int, real, bool, string, char)
    """
    @staticmethod
    @abstractmethod
    def primitive_type() -> type:
        pass

    @classmethod
    def default_typename(cls) -> str:
        return cls.primitive_type().__name__

    @classmethod
    def canonical_typename(cls) -> str:
        return cls.default_typename()

    def __init__(self, value):
        if not isinstance(value, self.primitive_type()):
            raise TypeError(f"Incorrect primitive type: '{type(value)}'.")
        else:
            super().__init__(value)

    @classmethod
    def build_from_data(cls, obj: t.Any, context: ResourceContext) -> DataType:
        if isinstance(obj, cls.primitive_type()):
            return cls(obj)
        else:
            raise TypeError(f"Unknown type: '{type(obj)}'.")


@DataType.set_resource_type(aliases=['int', 'integer'])
class Int(Primitive):

    @staticmethod
    def primitive_type() -> type:
        return int

    @classmethod
    def validate_data(cls, obj: t.Any, context: ResourceContext) -> TBoolStr:
        return primitive_validate(int)(obj)

    def __int__(self):
        return int(self.get_value())


@DataType.set_resource_type(aliases=['float', 'real'])
class Real(Primitive):

    @staticmethod
    def primitive_type() -> type:
        return float

    @classmethod
    def validate_data(cls, obj: t.Any, context: ResourceContext) -> TBoolStr:
        return primitive_validate(float)(obj)

    def __float__(self):
        return float(self.get_value())


@DataType.set_resource_type(aliases=['str', 'string'])
class String(Primitive):

    @staticmethod
    def primitive_type() -> type:
        return str

    @classmethod
    def validate_data(cls, obj: t.Any, context: ResourceContext) -> TBoolStr:
        return primitive_validate(str)(obj)

    def __str__(self):
        return str(self.get_value())


@DataType.set_resource_type(aliases=['bool', 'boolean'])
class Bool(Primitive):

    @staticmethod
    def primitive_type() -> type:
        return bool

    @classmethod
    def validate_data(cls, obj: t.Any, context: ResourceContext) -> TBoolStr:
        return primitive_validate(bool)(obj)

    def __bool__(self):
        return bool(self.get_value())