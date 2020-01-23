from CRIMSONCore.PropertyStorage import PropertyStorage
from CRIMSONSolver.ScalarProblem.ScalarBC import ScalarBC
from PythonQt import QtGui
from PythonQt.CRIMSON import Utils
import sympy
from sympy import *

class Scalar(PropertyStorage):
    def __init__(self):
        PropertyStorage.__init__(self)
        self.BCs = {}
        self.coefficients = {} #replace with string
        self.properties = [
            {
                "Scalar id number": 1
            },
            {
                "Scalar symbol": 'a'
            },
            {
                "Initial value": 0.0
            },
            {
                "Diffusion coefficient": 0.0
            }
        ]

    def setBC(self, faceIdentifier, scalarBC):  # for use in CPP code
        self.BCs[faceIdentifier] = scalarBC

    def getBC(self, faceIdentifier):  # for use in CPP code
        return self.BCs[faceIdentifier]

    def checkCoeffTerm(self, coeffTerm, coeffs):
        a = sympy.symbols(coeffs[0])
        if len(coeffs)>= 2:
            b = sympy.symbols(coeffs[1])
        if len(coeffs) >= 3:
            c = sympy.symbols(coeffs[2])
        if len(coeffs) >= 4:
            d = sympy.symbols(coeffs[3])
        if len(coeffs) > 4:
            QtGui.QMessageBox.critical(None, "Too many scalars",
                                       "\nThe number of scalars is greater than currently supported in flowsolver (4). All scalars beyond scalar {0} "
                                       "will be ignored".format(coeffs[3]))
        e = sympify(coeffTerm)
        Utils.logInformation(e.as_poly())
        coefficients_to_extract = [1, a, b, c, d, a*a, b*b, c*c, d*d, a*b, a*c, a*d, b*c, b*d, c*d]
        for index, mono in enumerate(coefficients_to_extract):
            try:
                # This will crash if coefficients_to_extract contains any symbols which are not part of e
                self.coefficients[index] = e.as_poly().coeff_monomial(mono)


            except Exception as e:
                QtGui.QMessageBox.critical(None, "Invalid format",
                                           "\nSyntax error in provided expression. Only symbols a, b, c, d and 2nd order polynomial terms allowed.")
                continue
        for c in self.coefficients:
            Utils.logInformation(self.coefficients[c])
        Utils.logInformation(self.coefficients)
        return self.coefficients

