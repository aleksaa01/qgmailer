from options import Options
from viewmodels._singleton import SingletonViewModel


class OptionsViewModel(metaclass=SingletonViewModel):

    def __init__(self):
        self.options = Options
        self.current_options = self.options.current_options()
        self.callback_map = {k:[] for k in self.current_options}

    def on_option_changed(self, option, callback):
        self.callback_map[option].append(callback)

    def new_options(self, options_map):
        old_options = self.current_options
        self.current_options = options_map
        for option, new_val in options_map.items():
            old_val = old_options[option]
            if new_val != old_val:
                self.options.change_option(option, new_val)
                self.notify(option, new_val)

        self.options.save()

    def possible_options(self):
        return self.options.possible_options()

    def current_value(self, option_name):
        return self.current_options[option_name]

    def notify(self, option, new_val):
        for callback in self.callback_map[option]:
            callback(new_val)
