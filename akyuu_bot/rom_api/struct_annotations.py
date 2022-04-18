class Annot(type):
    def __call__(cls):
        raise AttributeError("Cannot instantiate an annotation class")

    def __getattr__(cls, attr):
        if attr not in ('string', 'len'):
            raise AttributeError(
                f'Cannot access attribute {attr!r} for type {cls.__name__!r}')
        return object.__getattribute__(cls, attr)

    def __setattr__(self, attr, value):
        raise AttributeError(f'Cannot modify an annotation class')


class SubAnnotMeta(Annot):

    def __getitem__(self, x):
        dct = dict(self.__dict__)
        dct['len'] = x
        return SubAnnotMeta(f'{self.__name__}[{x}]', self.__bases__, dct)

    @property
    def string(self):
        return f'{self.len}{self.__dict__["string"]}'


class byte(bytes, metaclass=SubAnnotMeta):
    string = 's'


class u1(metaclass=Annot):
    string = '?'


class u8(int, metaclass=Annot):
    string = 'B'


class i8(int, metaclass=Annot):
    string = 'b'


class i16(int, metaclass=Annot):
    string = 'h'


class u16(int, metaclass=Annot):
    string = 'H'


class i32(int, metaclass=Annot):
    string = 'i'


class u32(int, metaclass=Annot):
    string = 'I'
