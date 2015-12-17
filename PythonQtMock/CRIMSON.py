def enum(**enums):
    return type('Enum', (), enums)

#: FaceType enumeration shows the type of a face
#: 
#: +-----------------+-------------------+
#: | Name            | Description       | 
#: +=================+===================+
#: |``ftCapInflow``  | inflow face       | 
#: +-----------------+-------------------+
#: | ``ftCapOutflow``| outflow face      | 
#: +-----------------+-------------------+ 
#: | ``ftWall``      | wall face         | 
#: +-----------------+-------------------+
#: |``ftUndefined``  | unknown face type | 
#: +-----------------+-------------------+
FaceType = enum(ftCapInflow=0, ftCapOutflow=1, ftWall=2, ftUndefined=3)

#: ArrayDataType enumeration shows the type of the data contained in an array
#: 
#: +-----------------+-------------------------+
#: | Name            | Description             | 
#: +=================+=========================+
#: |``Int``          | integer values          | 
#: +-----------------+-------------------------+
#: | ``Double``      | floating-poing values   | 
#: +-----------------+-------------------------+ 
ArrayDataType = enum(Int=0, Double=1)

class Utils:
    ''' 
    Utilities class containing static methods only. 
    
    The logging methods ``logInformation``, ``logWarning``, and ``logError`` will propagate the message
    with the corresponding error level to the CRIMSON application and will show up in the `Logging` view
    as well as in the console window. 
    
    Example usage::
    
        import PythonQt.CRIMSON.Utils as Utils
        Utils.logError('Failed to open file {0}'.format(filename))
    
    **Advanced**
    
    The ``reloadAll`` method will reload and recompile all solver-setup related python code.
    
    *Note*: for the changes to take effect, it is necessary to re-create the boundary conditions, 
    boundary condition sets, solver setups and solver studies if the corresponding class definitions have changed.
    
    '''

    @staticmethod
    def logInformation(m):
        ''' Log an information message. '''
        print(m)
        
    @staticmethod
    def logWarning(m):
        ''' Log a warning message. '''
        print(m)

    @staticmethod
    def logError(m):
        ''' Log an error message. '''
        print(m)
        
    @staticmethod
    def reloadAll():
        ''' Reload and recompile the python code. '''
        pass