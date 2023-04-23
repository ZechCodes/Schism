class SingletonClass:
    def __new__(cls, *_, **__):
        return cls
