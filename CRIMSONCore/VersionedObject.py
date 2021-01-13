from __future__ import print_function

"""
    This file serves as a means for how to implement backwards compatibility with data stored in Python objects.
    All solver objects that are saved to file should implement VersionedObject.
    
    Any object that implements VersionedObject will be handled specially by the code in CRIMSONCore/IO.py, 
    when an object that implements VersionedObject is loaded from file, it will run upgradeToLatest(),
    which will automatically add (or, perhaps, remove or convert) any fields as needed as the needs of Crimson change.
    
    It is the responsibility of individual objects to keep track of what changes are needed when going from one version to another.
    If an object does not implement upgradeObject, the default behavior will be to assume no upgrades are necessary.
    Some objects will probably very rarely change (BoundaryConditionSet),  
    whereas some other objects may change frequently (e.g., SolverStudy, SolverParameters3D both got updated for the Scalar UI).
    
    This versioning happens completely independently of the C++ side, however the C++ side will imply that the objects are all
    running the latest version. 
    
    For example, the C++ side may need to call a Python method that accesses a field that has been recently added.
    That method would likely crash if that field was not present. The C++ side is not prepared for this failure.
    
    Remember that a de-pickled Python object gets 
    - The latest methods from this version of PythonModules
    - Whatever fields the object was initialized with, some time in the distant past, with whatever version of PythonModules Crimson was using at the time.

    Note that the last time there was a major Python update (around 2017) I was not working on this project, if there are more versions that would benefit
    from backwards compatibility, unfortunately, I do not know of them. Maybe there are no projects from 2017 still in active use.

    [AJM] Jan. 2021

"""


def printNothing(*arg):
    pass

# To disable debug printouts, set debugPrint to printNothing
debugPrint = print

"""
    Static class that holds information about python module versions worth keeping track of
"""
class Versions:
    """
        Every time you add or remove a field to any object, make a new static field on this class.
    """
    Pre2021 = 'Pre2021'
    v2021A = '2021A'

    # the order in which upgrades should be applied
    Sequence = [Pre2021, v2021A]
    
    @staticmethod
    def indexOfVersion(versionToGetIndexOf):
        for versionIndex in range(len(Versions.Sequence)):
            version = Versions.Sequence[versionIndex]
            if(version == versionToGetIndexOf):
                return versionIndex
        
        # This would be a very hard thing to recover from. I am not really sure if there's a 'good' course of action for this.
        # This may be your only indication that you have, e.g., loaded a file from an incompatible branch, it's our responsibility to try and prevent this from happening.
        print('Error: Unknown version "', versionToGetIndexOf, '": no known upgrade path, leaving object as-is.', sep='')
        return -1

# Change this as needed when you add or remove fields from classes and need to preserve backwards compatibility with the original
def GetCurrentVersion():
    return Versions.v2021A

"""
    When a Python object is depickled, its fields get loaded as-is, which means that any fields that are added to a new version of Crimson will not be present.
    To mitigate that, this base class will provide an interface for adding these fields as necessary.

    From a pedantic CS perspective, the fields of an object are not part of the interface of the object and they should not be part of something that needs to
    be maintained consistently, but that is an API focused viewpoint, and when an object is mutated via pickle, it is not done via the public interface.

    Because of that, the fields are essentially a contract to be maintained, and this base implementation allows for that.
"""
class VersionedObject(object):
    """
        This init function will only be called for *newly created* solver objects, *not* previously saved objects loaded from file.
    """
    def __init__(self):
        # Pickle will load all the fields, so this should always be set to whatever the latest version of the interface is.
        # So just to be 100% clear, self.version will be depickled, this whole class is designed around the fact that Pickle 
        # deserializes only class fields, not methods or functions.
        self.version = GetCurrentVersion()

    """
        The default implementation assumes no upgrades are ever needed for any version.
        If you do not implement this for your classes, the code will assume the class is either brand new, or has never had any fields added/removed since it was created.
    """
    def upgradeObject(self, toVersion):
        fyi_fromVersion = self.getVersion()
        pass

    """
        This method will apply all upgrade steps to this object from the version it is at now, to the version the system is running.
    """
    def upgradeToLatest(self):
        fromVersion = self.getVersion()

        alreadyAtLatest = (fromVersion == GetCurrentVersion())
        if(alreadyAtLatest):
            debugPrint('Object ', self.__class__.__name__, ' does not need to be upgraded, already at system version.')
            return
              
        fromVersionIndex = Versions.indexOfVersion(fromVersion)
        if(fromVersionIndex < 0):
            debugPrint('Object ', self.__class__.__name__, ' not upgraded due to having an invalid version.')
            return
        
        # Apply upgrades for every version after this one
        startUpgradeIndex = fromVersionIndex + 1

        # Note: Python will not crash if you did something like range(900, len(someArray)) if someArray was a size of 10 or something
        for versionIndex in range(startUpgradeIndex, len(Versions.Sequence)):
            version = Versions.Sequence[versionIndex]
            self.upgradeObject(version)

        print('Upgraded object ', self.__class__.__name__, 'to', GetCurrentVersion())
        self.version = GetCurrentVersion()

    """
        The default implementation will assume any object that doesn't have a version is Pre2021.
        At the current time I am not aware of a need to add more "Pre2021" versions, but it could exist.
        A version like that would predate 2017, which is before my time unfortunately. 

        If this is necessary, the only way to get version information from objects older than 2021 would be to heuristically determine
        the object version using the presence or absence of fields, which can be done as needed, just override this method.
    """
    def getVersion(self):
        noVersionField = not hasattr(self, 'version')
        if(noVersionField):
            # Note: self.__class__.__name__ will actually get the name of the derived type.
            print('Object of type', self.__class__.__name__, 'has no version information, assuming this object is Versions.Pre2021')
            self.version = Versions.Pre2021

        return self.version

print('VersionedObject: System is using version ', GetCurrentVersion())