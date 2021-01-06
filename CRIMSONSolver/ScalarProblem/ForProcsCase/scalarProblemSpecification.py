"""
    This file contains helper functions that will not change depending on what values are entered from the UI.
    This file needs to be placed in 1-procs-case, alongside solver.inp
        This is NOT ran by the PythonModules. This is ran by the flowsolver.

    Be very careful about one based and zero based scalar indexes!

    For the sake of making it a bit clearer, I am using the following convention:
        scalarIndex: **Zero based** scalar Index, for Python. 
        scalarNumber: **One based** scalar identifier, this is used for communicating with the flowsolver.
            Generally any input or output to or from this script will be a scalarNumber, not a scalarIndex.

    AJM (Dec. 2020)
"""

from __future__ import print_function

# sympy may use numpy behind the scenes, so let's make sure we have it!
import numpy as np
from sympy import lambdify

# rather poor choice of naming on this sympy function
from sympy import symbols as create_sympy_symbols

from CRIMSONScalarProblem import AbstractRuntimeVectorHandler

"""
    This file contains configuration information from the UI. It should be in the same directory as this script.
"""
import generated_scalarProblemSpecification as Generated


"""
    Calculates the partial derivative of each expression, with respect to the symbol the expression relates to.

    Throws:
        KeyError: If an expression relates to an undefined scalar symbol
"""
def CalculateDerivativeOfExpressions(expressions, symbols):

    expressions_dSymbol = dict()

    for scalarName in expressions:
        if(scalarName not in symbols):
            raise KeyError('Scalar name ' + scalarName + ' is referenced in an expression but it is not present in symbols.')

        expression = expressions[scalarName]

        symbol = symbols[scalarName]

        expression_dSymbol = expression.diff(symbol)

        expressions_dSymbol[scalarName] = expression_dSymbol

    return expressions_dSymbol

"""
    Converts 
        a dictionary of <scalar name>:<sympy expression>
    to
        a dictionary of <scalar name>:<(numpy) lambda>
"""
def ExpressionsToLambdas(symbols, expressions, style = 'numpy'):
    reactionLambdas = dict()

    for scalarName in expressions:
        expression = expressions[scalarName]

        scalarLambda = lambdify(symbols.values(), expression, style)

        reactionLambdas[scalarName] = scalarLambda

    return reactionLambdas



ScalarIndexToName = Generated.ScalarNames

def GenerateNamesToIndexes():
    namesToIndexes = {}
    for nameIndex in range(len(ScalarIndexToName)):
        name = ScalarIndexToName[nameIndex]
        namesToIndexes[name] = nameIndex
    return namesToIndexes

ScalarNameToIndex = GenerateNamesToIndexes()

# Scalar numbers are one based in the flowsolver
def _scalarNumber(scalarIndex):
    return scalarIndex + 1

class ScalarProblemSpecification(AbstractRuntimeVectorHandler):

    def __init__(self, mpi_rank, timestepIndexAtConstruction):
        super(ScalarProblemSpecification, self).__init__(mpi_rank, timestepIndexAtConstruction)
        self.speciesIndexToFriendlyNamesMap = {}

        #substitute for
        #   self.speciesIndexToFriendlyNamesMap = {1: "Tf", 2: "X", 3: "Xa:Va", 4: "II", 5: "IIa", 6: "Xa:Va:II", 7: "mIIa", 8: "mIIa:ATIII", 9: "IIa:ATIII"}
        for scalarIndex in range(len(ScalarIndexToName)):
            self.speciesIndexToFriendlyNamesMap[_scalarNumber(scalarIndex)] = ScalarIndexToName[scalarIndex]

        #substitute for 
        #   self.setDiffusionCoefficientForSpecies(1, 10)
        #   self.setDiffusionCoefficientForSpecies(2, 10)
        #   ...
        for scalarName in Generated.DiffusionCoefficients:
            coefficientValue = Generated.DiffusionCoefficients[scalarName]
            scalarIndex = ScalarNameToIndex[scalarName]
            
            self.setDiffusionCoefficientForSpecies(_scalarNumber(scalarIndex), coefficientValue)


        #Substitute for:
        #    self.addNonlinearSolveStepToSpecies(1, [10,12,14,16,18])
        #    self.addNonlinearUpdateStepToSpecies(1, [11,13,15,17,19])
        # Remember: 0 based.
        currentIteration = Generated.NumberOfFluidIterations
        for iterationDict in Generated.Iterations:
            operationName = iterationDict["Operation"]
            iterationCount = iterationDict["Iterations"]

            scalarIndex = ScalarNameToIndex[operationName]
            
            
            solverIterations = []
            updateIterations = []

            for stepIterIndex in range(iterationCount):
                solverIterations.append(currentIteration)
                currentIteration += 1
                updateIterations.append(currentIteration)
                currentIteration += 1

            self.addNonlinearSolveStepToSpecies(_scalarNumber(scalarIndex), solverIterations)
            self.addNonlinearUpdateStepToSpecies(_scalarNumber(scalarIndex), updateIterations)

        # Reaction initialization:

        """
            A dictionary of all sympy symbols used in the reaction, this includes scalar symbols and reaction coefficients
        """
        self._symbols = Generated.Symbols

        print("Pre-calculating reaction equations....")
        
        """
            Expressions for the reaction of each scalar.
            These are provided so that you can do custom things with the expressions, e.g., take the derivative on the fly during a timestep's calculation.
            I precompute lambdas for the reactions and their derivatives, though, for speed reasons.
        """
        self._reactionExpressions = Generated.ReactionExpressions

        """
            Expressions for the partial derivative of each scalar's reaction, with respect to that scalar.
            These are provided so that you can do custom things with the expressions, e.g., take the derivative on the fly during a timestep's calculation.
            I precompute lambdas for the reactions and their derivatives, though, for speed reasons.
        """
        self._reactionGradientExpressions = CalculateDerivativeOfExpressions(self._reactionExpressions, self._symbols)

        """
            Lambdas representing the reaction for each scalar.
        """
        self._symbolLambdas = ExpressionsToLambdas(self._symbols, self._reactionExpressions)


        """
            Lambdas representing the derivative of the reaction for each scalar, with respect to the scalar.
        """
        self._symbolGradientLambdas = ExpressionsToLambdas(self._symbols, self._reactionGradientExpressions)

    """
        Throws only on internal error conditions: 
            RuntimeError: If `self._symbols` is out of sync with `ReactionCoefficients` and `ScalarNames`
            RuntimeError: If you or I made a typo in this method and didn't set `value` to anything
            RuntimeError: if a symbol does not have a state vector associated with it in the flowsolver

        Gets an array containing the current state of each scalar, plus the constants.
        Of the form:
        [<constant value>, <constant value>, ..... <scalar value>, <scalar value>, ....]

        Where the size of the array and the order of these items MUST match the order of of items in symbols

        For ease of validation I decided to have this also return an array of symbol names.

    """
    def getSymbolStateArray(self):
        symbolNameArray = []
        valueArray = []

        for symbolName in self._symbols:

            value = None

            # Detect what type of symbol it is, then get the (current) value of this symbol.
            if(symbolName in ScalarIndexToName):
                # The concentration of each scalar does change through the course of the simulation, so we 
                # should use the scalar state dictionary to get the scalar values at this iteration
                scalarNumber = _scalarNumber(ScalarNameToIndex[symbolName])

                if(scalarNumber not in self.scalarStateVectorsDictionary):
                    raise RuntimeError('Scalar number {} could not be found in scalarStateVectorsDictionary. Contents of dictionary: {}'.format(scalarNumber, self.scalarStateVectorsDictionary.keys()))

                value = self.scalarStateVectorsDictionary[scalarNumber]
                
            elif(symbolName in Generated.ReactionCoefficients):
                # The value of these constants does not change through the course of the simulation, so we can just grab the generated value
                value = Generated.ReactionCoefficients[symbolName]

            else:
                raise RuntimeError("Unexpected error: Symbol '" + symbolName + "' is in the _symbols list but is not a reaction coefficient or scalar.")

            # Need to use is, because for some reason numpy overloaded the == None check to say "is every element None", that's not what I meant
            if(value is None):
                # this is really just here to protect us if we happen to add another elif but forget to set value to something in it
                raise RuntimeError("Unexpected error: Failed to set a value for symbol '" + symbolName + "'")

            valueArray.append(value)
            symbolNameArray.append(symbolName)

        assert(len(self._symbols) == len(valueArray))
        assert(len(valueArray) == len(symbolNameArray))

        return (valueArray, symbolNameArray) 
    
    """
        Throws:
            KeyError if `scalarNumber` is not in `self.scalarStateVectorsDictionary`
    """
    def getScalarMatrixShape(self, scalarNumber):
        if(scalarNumber not in self.scalarStateVectorsDictionary):
            raise KeyError('Scalar number ' + str(scalarNumber) + ' is not known to this scalar problem specification.')

        value = self.scalarStateVectorsDictionary[scalarNumber]

        return value.shape


    """
        Warning: scalarNumber is 1 based!
        Throws:
            KeyError: If `scalarNumber` is not defined in this scalar problem specification
            KeyError: If `scalarNumber` is  < 1 (enforces that this must be 1 based and prevents indexing of -1)
    """
    def computeScalarLHSorRHSVectorForOneSpecies(self, reactionTermOutput, scalarNumber, computeGradient):
        if(scalarNumber > len(ScalarIndexToName)):
            print('Number of Scalars:', len(ScalarIndexToName))
            print(ScalarIndexToName)
            raise KeyError('ScalarNumber ' + str(scalarNumber) + ' is not known to this scalar problem specification.')

        if(scalarNumber < 1):
            raise KeyError('Unexpected scalarNumber {}. Expected a 1 based scalar number.'.format(scalarNumber))
        
        scalarName = ScalarIndexToName[scalarNumber - 1]

        print('Scalar to be computed: "', scalarName, '" (scalarNumber=', scalarNumber, ')', sep ='')



        (symbolStateArray, symbolNameArray) = self.getSymbolStateArray()

        assert(len(symbolStateArray) == len(symbolStateArray))
        print('The values for this iteration are:')
        
        for symbolIndex in range(len(symbolStateArray)):
            # For debugging purposes only, this print statement will get very out of hand for real meshes
            print('[',symbolIndex,'] "', symbolNameArray[symbolIndex], '" = ', symbolStateArray[symbolIndex], sep = '')
            pass


        lambdaToRun = None

        if(computeGradient):
            lambdaToRun = self._symbolGradientLambdas[scalarName]
            scalarPolynomial = self._reactionGradientExpressions[scalarName]
            print('Expression:')
            print(scalarName, ' = ', scalarPolynomial, sep='')
        else:
            scalarPolynomial = self._reactionExpressions[scalarName]
            print('Expression:')
            print(scalarName, ' = ', scalarPolynomial, sep='')
            lambdaToRun = self._symbolLambdas[scalarName]

        result = lambdaToRun(*symbolStateArray)

        print('Result of lambda:', result)

        # NOTE: result could be just 0, not [0], e.g., if the gradient resolved to 0 because there were no instances of symbol 'I' need to handle that        
        resultIsArray = hasattr(result, '__getitem__')
        
        # TODO: does a reaction that resolves to some constant k1 mean that the concentration of a scalar should be set to that at all nodes?
        if(resultIsArray):
            reactionTermOutput[:] = result[:]
        
        else:
            oldScalarShape = self.getScalarMatrixShape(scalarNumber)
            print("Note: lambda returned non-array value, returning constant value for all nodes")
            reactionTermOutput[:] = np.ones(oldScalarShape)*result

    def clearCalculatorCache(self):
        self.scalar1CoefficientsSet = False
        self.scalar2CoefficientsSet = False
