import io
from typing import Type, ClassVar, Union, TypeVar

from .structs import Struct


T = TypeVar('T', bound=Struct)


class Pointer(int):
    """
    Pointer[T]: A generic class for representing pointers to ROM data.
    """
    type: Type[Struct]
    size: int
    string: ClassVar[str] = 'I'

    def __new__(cls, address: int):
        obj = super().__new__(cls, address)
        obj.size = cls.type.size
        return obj

    def __add__(self: 'Pointer[T]', other: int) -> 'Pointer[T]':
        return self.__class__(super().__add__(other * self.size))

    def __sub__(self: 'Pointer[T]', other: int) -> 'Pointer[T]':
        return self.__class__(super().__sub__(other * self.size))

    def __repr__(self) -> str:
        return hex(self)

    def __class_getitem__(cls, item: Type[Struct]) -> Type:
        class _Ptr(cls):
            type = item

            __class_getitem__ = None

        _Ptr.__name__ = f'{cls.__name__}[{item.__name__}]'
        _Ptr.__qualname__ = f'{cls.__qualname__}[{item.__name__}]'
        _Ptr.__doc__ = cls.__doc__
        return _Ptr


class Rom(bytes):
    def __new__(cls, dat: bytes):
        return super().__new__(cls, dat)

    def create_stream(self):
        return io.BytesIO(self)

    def deref(self, ptr: Pointer[T]) -> T:
        addr = ptr & 0x00ffffff
        return ptr.type(super().__getitem__(slice(addr, addr + ptr.size)))





