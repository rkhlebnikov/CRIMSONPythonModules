import cPickle

def saveToFile(obj, filename):
    with open(filename, 'wb') as f:
        cPickle.dump(obj, f)

def loadFromFile(filename):
    with open(filename, 'rb') as f:
        return cPickle.load(f)


