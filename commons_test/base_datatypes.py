from application.resources import *


@DataType.set_resource_type()
class Dummy(ReferrableDataType):
    """
    Dummy class for testing.
    """

    def __init__(self, x: int, y: str, z: bool):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"Dummy[x = {self.x}; y = \"{self.y}\"; z = {self.z}]"


@DataType.set_resource_type()
class SuperDummy(ReferrableDataType):
    """
    "Super"-Dummy class for testing references.
    """
    def __init__(self, name: str, desc: str, dummy: Dummy):
        self.name = name
        self.desc = desc
        self.dummy = dummy

    def __repr__(self):
        return f"SuperDummy[name = {self.name}; desc = {self.desc}; dummy = {self.dummy}]"