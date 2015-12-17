import time
from PythonQt.CRIMSON import Utils

__author__ = 'rk13'


class Timer:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        elapsed = time.time() - self.start
        Utils.logInformation('{} in {} ms'.format(self.name, int(elapsed * 1000)))