import os

__author__ = 'rk13'


class FileList(object):
    def __init__(self, folder):
        self.folder = folder
        self.openFiles = {}

    def __getitem__(self, openFileInfo):
        if isinstance(openFileInfo, tuple):
            name = openFileInfo[0]
            openmode = openFileInfo[1]
        else:
            name = openFileInfo
            openmode = 'wt'

        if name not in self.openFiles:
            self.openFiles[name] = open(os.path.join(self.folder, name), openmode)
        return self.openFiles[name]

    def isOpen(self, fileName):
        return self.openFiles.__contains__(fileName)

    def close(self):
        for _, f in self.openFiles.iteritems():
            f.close()