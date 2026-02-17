import operator


class WrapperObject:
    __slots__ = "__original__"

    def __init__(self, original):
        self.__setattr__("__original__", original)
        try:
            object.__setattr__(self, "__qualname__", original.__qualname__)
        except AttributeError:
            pass

    @property
    def __name__(self):
        return self.__original__.__name__

    @__name__.setter
    def __name__(self, value):
        self.__original__.__name__ = value

    @property
    def __class__(self):
        return self.__original__.__class__

    @__class__.setter
    def __class__(self, value):
        self.__original__.__class__ = value

    @property
    def __annotations__(self):
        return self.__original__.__annotations__

    @__annotations__.setter
    def __annotations__(self, value):
        self.__original__.__annotations__ = value

    @property
    def __module__(self):
        return self.__original__.__module__

    @__module__.setter
    def __module__(self, value):
        self.__original__.__module__ = value

    @property
    def __doc__(self):
        return self.__original__.__doc__

    @__doc__.setter
    def __doc__(self, value):
        self.__original__.__doc__ = value

    def __dir__(self):
        return dir(self.__original__)

    def __str__(self):
        return str(self.__original__)

    def __repr__(self):
        return "<{} at 0x{:x} for {} at 0x{:x}>".format(
            type(self).__name__, id(self), type(self.__original__).__name__, id(self.__original__)
        )

    def __reversed__(self):
        return reversed(self.__original__)

    def __round__(self):
        return round(self.__original__)

    def __lt__(self, other):
        return self.__original__ < other

    def __le__(self, other):
        return self.__original__ <= other

    def __eq__(self, other):
        return self.__original__ == other

    def __ne__(self, other):
        return self.__original__ != other

    def __gt__(self, other):
        return self.__original__ > other

    def __ge__(self, other):
        return self.__original__ >= other

    def __hash__(self):
        return hash(self.__original__)

    def __nonzero__(self):
        return bool(self.__original__)

    def __bool__(self):
        return bool(self.__original__)

    def __setattr__(self, name, value):
        if name.startswith("_apm_"):
            object.__setattr__(self, name, value)

        elif name == "__original__":
            object.__setattr__(self, name, value)
            try:
                object.__delattr__(self, "__qualname__")
            except AttributeError:
                pass
            try:
                object.__setattr__(self, "__qualname__", value.__qualname__)
            except AttributeError:
                pass

        elif name == "__qualname__":
            setattr(self.__original__, name, value)
            object.__setattr__(self, name, value)

        else:
            setattr(self.__original__, name, value)

    def __getattr__(self, name):
        # If we are being to lookup '__original__' then the
        # '__init__()' method cannot have been called.
        if name == "__original__":
            raise ValueError("Original object has not been assigned")
        if name.startswith("_apm_"):
            return object.__getattribute__(self, name)
        return getattr(self.__original__, name)

    def __delattr__(self, name):

        if name == "__original__":
            raise TypeError("__original__ must be an object")

        elif name == "__qualname__":
            object.__delattr__(self, name)
            delattr(self.__original__, name)

        elif not hasattr(self.__original__, name):
            object.__delattr__(self, name)

        else:
            delattr(self.__original__, name)

    def __add__(self, other):
        return self.__original__ + other

    def __sub__(self, other):
        return self.__original__ - other

    def __mul__(self, other):
        return self.__original__ * other

    def __div__(self, other):
        return self.__original__ / other

    def __truediv__(self, other):
        return operator.truediv(self.__original__, other)

    def __floordiv__(self, other):
        return operator.floordiv(self.__original__ // other)

    def __mod__(self, other):
        return self.__original__ % other

    def __divmod__(self, other):
        return divmod(self.__original__, other)

    def __pow__(self, other, *args):
        return pow(self.__original__, other, *args)

    def __lshift__(self, other):
        return self.__original__ << other

    def __rshift__(self, other):
        return self.__original__ >> other

    def __and__(self, other):
        return self.__original__ & other

    def __xor__(self, other):
        return self.__original__ ^ other

    def __or__(self, other):
        return self.__original__ | other

    def __radd__(self, other):
        return other + self.__original__

    def __rsub__(self, other):
        return other - self.__original__

    def __rmul__(self, other):
        return other * self.__original__

    def __rdiv__(self, other):
        return operator.div(other, self.__original__)

    def __rtruediv__(self, other):
        return operator.truediv(other, self.__original__)

    def __rfloordiv__(self, other):
        return other // self.__original__

    def __rmod__(self, other):
        return other % self.__original__

    def __rdivmod__(self, other):
        return divmod(other, self.__original__)

    def __rpow__(self, other, *args):
        return pow(other, self.__original__, *args)

    def __rlshift__(self, other):
        return other << self.__original__

    def __rrshift__(self, other):
        return other >> self.__original__

    def __rand__(self, other):
        return other & self.__original__

    def __rxor__(self, other):
        return other ^ self.__original__

    def __ror__(self, other):
        return other | self.__original__

    def __iadd__(self, other):
        self.__original__ += other
        return self

    def __isub__(self, other):
        self.__original__ -= other
        return self

    def __imul__(self, other):
        self.__original__ *= other
        return self

    def __idiv__(self, other):
        self.__original__ = operator.idiv(self.__original__, other)
        return self

    def __itruediv__(self, other):
        self.__original__ = operator.itruediv(self.__original__, other)
        return self

    def __ifloordiv__(self, other):
        self.__original__ //= other
        return self

    def __imod__(self, other):
        self.__original__ %= other
        return self

    def __ipow__(self, other):
        self.__original__ **= other
        return self

    def __ilshift__(self, other):
        self.__original__ <<= other
        return self

    def __irshift__(self, other):
        self.__original__ >>= other
        return self

    def __iand__(self, other):
        self.__original__ &= other
        return self

    def __ixor__(self, other):
        self.__original__ ^= other
        return self

    def __ior__(self, other):
        self.__original__ |= other
        return self

    def __neg__(self):
        return -self.__original__

    def __pos__(self):
        return +self.__original__

    def __abs__(self):
        return abs(self.__original__)

    def __invert__(self):
        return ~self.__original__

    def __int__(self):
        return int(self.__original__)

    # Python3 has no long, it is replaced by int in python3.0 and above
    def __long__(self):
        return int(self.__original__)

    def __float__(self):
        return float(self.__original__)

    def __complex__(self):
        return complex(self.__original__)

    def __oct__(self):
        return oct(self.__original__)

    def __hex__(self):
        return hex(self.__original__)

    def __index__(self):
        return operator.index(self.__original__)

    def __len__(self):
        return len(self.__original__)

    def __contains__(self, value):
        return value in self.__original__

    def __getitem__(self, key):
        return self.__original__[key]

    def __setitem__(self, key, value):
        self.__original__[key] = value

    def __delitem__(self, key):
        del self.__original__[key]

    def __getslice__(self, i, j):
        return self.__original__[i:j]

    def __setslice__(self, i, j, value):
        self.__original__[i:j] = value

    def __delslice__(self, i, j):
        del self.__original__[i:j]

    def __enter__(self):
        return self.__original__.__enter__()

    def __exit__(self, *args, **kwargs):
        return self.__original__.__exit__(*args, **kwargs)

    def __iter__(self):
        return iter(self.__original__)

    def __reduce__(self):
        return self.__original__.__reduce__()

    def __reduce_ex__(self, protocol):
        return self.__original__.__reduce_ex__(protocol)

    def __sizeof__(self):
        return self.__original__.__sizeof__()
