import inspect
from collections import MutableMapping


class MissingVarException(Exception):
    pass


class MultiSourceDict(MutableMapping):
    def __init__(self, data, obj=None):
        self.data = data

        self.obj = obj
        self.obj_conf_keys = set()
        for name, value in inspect.getmembers(self.obj):
            if hasattr(value, '_is_conf'):
                self.obj_conf_keys.add(name)

        self.conf_keys = set(self.data.keys())
        self.conf_keys.update(self.obj_conf_keys)

    def get_value(self, name):
        if name in self.obj_conf_keys:
            # delete to avoid recursion
            self.obj_conf_keys.remove(name)
            r = getattr(self.obj, name)()
            self.obj_conf_keys.add(name)
            return r
        if name in self.data:
            return self.data[name]
        raise MissingVarException()

    def set_value(self, name, value):
        self.data[name] = value

    def __setitem__(self, key, value):
        self.set_value(key, value)

    def __getitem__(self, key):
        try:
            return self.get_value(key)
        except MissingVarException:
            raise KeyError(key)

    def __delitem__(self, key):
        raise NotImplementedError()

    def __iter__(self):
        return iter(self.conf_keys)

    def __len__(self):
        return len(self.conf_keys)

    def __getattr__(self, name):
        try:
            return self.get_value(name)
        except MissingVarException:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in ['data', 'obj', 'obj_conf_keys', 'conf_keys']:
            self.__dict__[name] = value
        else:
            self.set_value(name, value)


def conf(func):
    func._is_conf = True
    return func