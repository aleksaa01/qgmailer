from os.path import splitext as split_extension

from PySide2.QtCore import QThread, Signal


class BaseFetcher(QThread):

    threadFinished = Signal(list)
    ACCEPTABLE_FILETYPES = ('.json', '.p', '.pickle')

    def __init__(self, resource, filename='', parent=None):
        super().__init__(parent)

        self.res = resource
        if filename == '' or self._check_filetype(filename):
            self.filename = filename
        else:
            raise ValueError('Got filename with wrong file type'
                'Acceptable file types:', ', '.join(self.ACCEPTABLE_FILETYPES))

    def _check_filetype(self, filename):
        if split_extension(filename) in self.ACCEPTABLE_FILETYPES:
            return True
        return False

    def run(self):
        raise NotImplementedError('run is not implemented yet.')

    def load_from_api(self):
        raise NotImplementedError('load_from_api is not implemented yet.')

    def load_from_file(self):
        raise NotImplementedError('load_from_file is not implemented yet.')
