from .base_datatypes import Dummy, SuperDummy
from resources import *


@DataType.set_resource_type()
class DummyGen(Generator):

    @classmethod
    def formal_parameters(cls) -> set[Parameter]:
        return {
            Parameter('x', Int, 'Integer parameter.', True),
            Parameter('y', String, 'String parameter.', True),
            Parameter('z', Bool, 'Boolean parameter.', True),
        }

    @staticmethod
    def target_type() -> t.Type[ReferrableDataType]:
        return DataType.get_type('Dummy') or Dummy

    @classmethod
    def build_from_data(cls, obj: t.Any, context: ResourceContext) -> DataType:
        """
        {
            "name": ...,
            "parameters": ...,
        }
        :param obj:
        :param context:
        :return:
        """
        if isinstance(obj, cls):
            return obj
        elif isinstance(obj, dict):
            check = all(name in obj for name in ['name', 'parameters'])
            if not check:
                raise ValueError('Missing parameters from generator description.')
            else:
                if DataType.get_generator_type(obj['name']) != cls:
                    raise TypeError('Wrong generator type.')
                else:
                    given_params = obj['parameters']
                    inputs: dict[str, DataType] = {key: None for key in given_params}
                    for param in cls.actual_parameters(given_params):
                        inputs[param.name] = param.build(given_params[param.name], context)
                    for key in inputs:
                        value = inputs[key]
                        if type(value).is_primitive():
                            inputs[key] = t.cast(Primitive, value).get_value()
                    dummy_class = DataType.get_type('Dummy')
                    # noinspection PyArgumentList
                    return dummy_class(**inputs)
        else:
            raise TypeError(f"Unknown type: '{type(obj)}'.")


@DataType.set_resource_type()
class SuperDummyGen(Generator):

    @classmethod
    def formal_parameters(cls) -> set[Parameter]:
        return {
            Parameter('name', String, 'Name.', True),
            Parameter('desc', String, 'Description.', True),
            Parameter('dummy', DataType.get_type('Dummy'), 'Dummy.', True),
        }

    @staticmethod
    def target_type() -> t.Type[ReferrableDataType]:
        return DataType.get_type('SuperDummy') or SuperDummy

    @classmethod
    def build_from_data(cls, obj: t.Any, context: ResourceContext) -> DataType:
        if isinstance(obj, cls):
            return obj
        elif isinstance(obj, dict):
            check = all(name in obj for name in ['name', 'parameters'])
            if not check:
                raise ValueError('Missing parameters from generator description.')
            else:
                if DataType.get_generator_type(obj['name']) != cls:
                    raise TypeError('Wrong generator type.')
                else:
                    given_params = obj['parameters']
                    inputs: dict[str, DataType] = {key: None for key in given_params}
                    for param in cls.actual_parameters(given_params):
                        inputs[param.name] = param.build(given_params[param.name], context)
                    for key in inputs:
                        value = inputs[key]
                        if type(value).is_primitive():
                            inputs[key] = t.cast(Primitive, value).get_value()
                    super_dummy_class = DataType.get_type('SuperDummy')
                    # noinspection PyArgumentList
                    return super_dummy_class(**inputs)
        else:
            raise TypeError(f"Unknown type: '{type(obj)}'.")