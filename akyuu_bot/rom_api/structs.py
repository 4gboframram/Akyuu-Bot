import struct
from typing import Optional


def wraps(cls, wrapped):
    cls.__annotations__ = wrapped.__annotations__
    cls.__doc__ = wrapped.__doc__
    cls.__name__ = wrapped.__name__
    cls.__qualname__ = wrapped.__qualname__
    return cls


class StructMeta(type):
    def __init__(cls, *args):
        cls.__slots__ = tuple(list(cls.__annotations__) + ['_struct', '_data'])
        struct_str = '<' + ''.join(i.string for i in cls.__annotations__.values())
        _struct = struct.Struct(struct_str)
        cls._struct = _struct
        cls.size = _struct.size
        super().__init__(*args)


class Struct:
    """
    A base class used to represent structures of in rom data
    """
    _struct: struct.Struct  # make the static type checker happy
    size: int

    def __init__(self, dat: Optional[bytes] = None, **kwargs):

        if dat is None:
            assert set(kwargs) == set(self.__annotations__)
            fields = {attr: kwargs[attr] for attr in self.__annotations__}  # order the kwargs
            self._data = self._struct.pack(*fields.values())
            [object.__setattr__(self, attr, val) for attr, val in zip(self.__annotations__, (i for i in fields.values()))]
        else:
            self._data: bytes = dat
            unpacked = self._struct.unpack(dat)
            [object.__setattr__(self, attr, val) for attr, val in zip(self.__annotations__, unpacked)]

    def __repr__(self):
        attrs = ', '.join(f'{attr}={getattr(self, attr)}' for attr in self.__annotations__)
        return f'{self.__class__.__name__}({attrs})'

    def __setattr__(self, key, value):
        if key in self.__annotations__:
            raise AttributeError(f"{self.__class__.__name__!r} objects are read only")
        object.__setattr__(self, key, value)


def make_struct(cls):  # not recommended because the static type checker doesn't like it

    class Wrapper(Struct, cls, metaclass=StructMeta):
        pass
    return wraps(Wrapper, cls)


__all__ = ['make_struct', 'Struct', 'StructMeta', 'wraps']
