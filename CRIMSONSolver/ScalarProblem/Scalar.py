from __future__ import print_function
from CRIMSONCore.PropertyStorage import PropertyStorage

"""
    I don't want to get *too* picky about this, this is meant to catch typos,
    it's not a guarantee that your reaction will work.

    Will accept:
        - int
        - float
        - bool
    
    Will return false always on:
        - string
        - set/list/dict
        - None
"""
def isValueNumeric(value):
    # Special case for string to prevent unexpected conversions
    if(isinstance(value, str)):
        return False
    
    try:
        valueFloat = float(value)
        return True
    except:
        return False

def stripNewlines(string):
    return string.replace('\n', '')
        

class Scalar(PropertyStorage):
    '''
    A class representing a scalar quantity in a RAD problem
    '''
    def __init__(self):
        PropertyStorage.__init__(self)
        self.properties = [
                {
                    "Diffusion coefficient": 1.1
                },
                {
                    # Set this to true to have residuals be factored in by the flowsolver
                    # (as of Dec. 2020 this is not implemented in the flowsolver and this flag will have no effect)
                    "Residual control": False,
                },
                {
                    "Residual criteria": 0.001,
                    "attributes": {"minimum": 0.0}
                },

            # I am deliberately not including ScalarSymbol as a PropertyStorage property, because it needs special treatment and validation before being renamed,
            # the UI renames the node and checks for duplicates.
            #
            # I could hook into the property changed event, but it seems easier to just not show it in the property tree.
        ]

        # Qt is very heavily invested in Unicode
        self._scalarSymbol = u"new Scalar"
        self._reactionString = u""

    def getScalarSymbol(self):
        return self._scalarSymbol
    
    def setScalarSymbol(self, scalarSymbol):
        self._scalarSymbol = scalarSymbol

    """
        This returns the reaction string with any newlines the user inserted. 
        Note that the python modules will strip out newlines before writing it to the scalarProblemSpecification
    """
    def getReactionString(self):
        return self._reactionString
    
    def setReactionString(self, reactionString):
        self._reactionString = reactionString

    """
        Reaction equation with newlines stripped out
    """
    def getReaction_SingleLine(self):
        return self._reactionString.replace('\n', '')

    """
        Note: this is safe in Python 3
    """
    def testRunReaction(self, symbols, reactionEquation):
        reactionEquation_NoNewline = stripNewlines(reactionEquation)
        if("" == reactionEquation_NoNewline):
            print('Reaction equation cannot be left blank.')
            return False

        invalidSymbols = {"#", "'", '"'}

        for invalidSymbol in invalidSymbols:
            if(invalidSymbol in reactionEquation_NoNewline):
                print("Reaction equation '", reactionEquation_NoNewline, "' contains an invalid symbol '", invalidSymbol, "'.", sep='')
                return False

        symbolValue = 2
        for symbol in symbols:
            # Assign all the symbols as local variables
            exec('{}={}'.format(symbol,symbolValue))
            
        try:
            result = eval(reactionEquation_NoNewline)

            if(not isValueNumeric(result)):
                raise RuntimeError('Value did not evaluate to a numeric result, instead it evaluated to a value of type {}'.format(type(result)))

            print('Reaction equation "', reactionEquation_NoNewline, '" with symbols ', symbols, ' and all symbols set to ', symbolValue, ' evaluated to ', result, sep='')
            return True

        except Exception as ex:
            print('Failed to evaluate reaction equation "', reactionEquation_NoNewline, '" with symbols ', symbols, ': ', ex.message, sep='')
            return False