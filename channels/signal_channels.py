
class SignalChannel(object):
    def __init__(self, *list_of_arg_types):
        self.arg_types = list_of_arg_types
        self.listeners = []

    def connect(self, callback):
        self.listeners.append(callback)

    def emit(self, *args):
        if len(args) != len(self.arg_types):
            raise ValueError("Invalid number of arguments.")
        for arg, type in zip(args, self.arg_types):
            if not isinstance(arg, type):
                raise TypeError(f"Invalid type for: {arg}. Expected {type}, got {type(arg)}.")

        for listener in self.listeners:
            listener(*args)
