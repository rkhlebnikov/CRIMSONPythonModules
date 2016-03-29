class PropertyAccessor(object):
    def __init__(self, propertyList):
        self.propertyList = propertyList

    @staticmethod
    def getNameAndValueKey(property):
        if "name" in property: # Support for old property definition syntax, i.e. {"name": "Pressure", "value": 100.0}
            return (property["name"], "value")
        for key in property: # Support for new property definition syntax, i.e. {"Pressure": 100.0}
            if key != "attributes":
                return (key, key)

    @staticmethod
    def findItemIndex(propertyList, itemName):
        for i, property in enumerate(propertyList):
            propertyName, propertyValueKey = PropertyAccessor.getNameAndValueKey(property)
            if propertyName.lower() == itemName.lower():
                return (propertyList, i, propertyValueKey)
            if isinstance(property[propertyValueKey], list):
                result = PropertyAccessor.findItemIndex(property[propertyValueKey], itemName)
                if result is not None:
                    return result

    def __getitem__(self, itemName):
        propertyListAndIndexAndValueKey = PropertyAccessor.findItemIndex(self.propertyList, itemName)
        if propertyListAndIndexAndValueKey is None:
            raise KeyError("Item with name '" + itemName + "' not found")

        propertyList, index, valueKey = propertyListAndIndexAndValueKey
        value = propertyList[index][valueKey]
        if isinstance(value, list):
            return PropertyAccessor(value)
        return value


    def __setitem__(self, itemName, value):
        propertyListAndIndexAndValueKey = PropertyAccessor.findItemIndex(self.propertyList, itemName)
        if propertyListAndIndexAndValueKey is None:
            raise KeyError("Item with name '" + itemName + "' not found")

        propertyList, index, valueKey = propertyListAndIndexAndValueKey
        propertyValue = propertyList[index][valueKey]

        if isinstance(propertyValue, list):
            raise TypeError("It is forbidden to modify the property lists")

        if type(propertyValue) != type(value):
            raise TypeError("It is forbidden to change the type of properties. Expected " + type(
                propertyValue).__name__ + ", received " + type(value).__name__)

        propertyList[index][valueKey] = value


class PropertyStorage(object):
    '''
    The PropertyStorage class is a convenience class for communicating the various properties of a boundary condition
    or solver parameters to the C++ code for the user to edit.

    The property is defined as a dictionary which must contain at least one string key with a value.
    The type of the property value is determined by the type of value itself::

        {
            "IntegerProperty": 42
        }

    will define a property with an integer value, whereas ::

        {
            "DoubleProperty": 42.0
        }

    will define a property with a floating-point value.

    Each property can also have multiple attributes that affect the user interaction for value editing, such as
    minimum and maximum values, stored in a dictionary::

        {
            "PropertyWithAttributes": 42,
            "attributes": {"minumum": 3, "maximum": 100}
        }

    The types of properties and their attributes are described in section `Property reference`_.

    In addition to value-properties, various properties can also be grouped. The group is a property, whose value
    attribute is a list of other properties::

        {
            "Group": [
                {
                    "Property 1": 0
                },
                {
                    "Property 2": 5.0
                }
            ]
        }

    Group properties can also be nested.

    The ``PropertyStorage.properties`` is a top-level group which contains all the properties for a boundary condition or
    solver parameters.

    All the properties should be defined in the constructor of the class inheriting from ``PropertyStorage`` and cannot be
    changed at run time. Here's a complete example of defining a solver parameters with multiple grouped parameters::

        class SolverParameters(PropertyStorage):
        def __init__(self):
            PropertyStorage.__init__(self)
            self.properties = [
                {
                    "Time parameters": [
                        {
                            "Number of time steps": 200,
                            "attributes": {"minimum": 1}
                        },
                        {
                            "Time step size": 0.01,
                            "attributes": {"minimum": 0.0, "suffix": " s"}
                        }
                    ]
                },
                {
                    "Fluid parameters": [
                        {
                            "Viscosity": 0.004,
                            "attributes": {"minimum": 0.0, "suffix": u" g/(mm\u00B7s)"}
                        },
                        {
                            "Density": 0.00106,
                            "attributes": {"minimum": 0.0, "suffix": u" g/mm\u00B3"}
                        }
                    ]
                },
            ]

.. _`Property reference`:

    **Property reference**

    Each property is a dictionary with a required keys-value pair from property name to its value, and an optional key ``attributes``::

        {
            str: value_type,
            "attributes": dict
        }

    The attributes only affect the user interaction with a GUI element representing the value.
    The attributes available for each property type are described below.

    *Integer property*

        ``value_type`` is ``int``. Represented as a spin box.

        Attributes
            :minimum: ``int`` minimum value (default: minimum representable ``int``).
            :maximum: ``int`` maximum value (default: maximum representable ``int``).
            :prefix: ``str`` the prefix to be added before the value (default: ``""``).
            :suffix: ``str`` the suffix to be added after the value (default: ``""``). For example, measurement unit.
            :singleStep: ``int`` a single step for increment/decrement buttons (default: ``1``).

        Example::

            {
                "Number of time steps": 200,
                "attributes": {
                    "minimum": 1,
                    "maximum": 10000,
                    "prefix": "",
                    "suffix": " s",
                    "singleStep": 5
                    }
            },

    *Floating-point property*

        ``value_type`` is ``float``. Represented as a double-valued spin box.

        Attributes
            :minimum: ``float`` minimum value (default: minimum representable ``float``).
            :maximum: ``float`` maximum value (default: maximum representable ``float``).
            :prefix: ``str`` the prefix to be added before the value (default: ``""``).
            :suffix: ``str`` the suffix to be added after the value (default: ``""``). For example, measurement unit.
            :singleStep: ``float`` a single step for increment/decrement buttons (default: ``1.0``).
            :decimals: ``int`` the displayed precision of the floating point value (default: ``50``).
                       Only necessary digits are displayed, i.e. ``1.5`` will be shown and not ``1.50000000``.

        Example::

            {
                "Viscosity": 0.004,
                "attributes": {
                    "minimum": 0.0,
                    "maximum": 100.0,
                    "prefix": "",
                    "suffix": u" g/(mm\u00B7s)",
                    "singleStep": 0.1,
                    "decimals": 2
                    }
            }

    *Boolean property*
        ``value_type`` is ``bool``. Represented as a check box with text for ``True`` and ``False`` values.

        Attributes
            - None

        Example::

            {
                "Residual control": True,
            }

    *String property*
        ``value_type`` is ``str``. Represented as a text edit.

        Attributes
            - None

        Example::

            {
                "Simulation name": "Great simulation",
            }

    *Enumeration property*
        ``value_type`` is ``int``. The enumeration properties are ``int`` properties that also have the ``enumNames``
        attribute. Represented as a combo-box with the items to be selected.

        Attributes
            :enumNames: ``list`` A list of strings that correspond to the values of the enumeration.

        Example::

            class CouplingType(object):
                enumNames = ["Explicit", "Implicit", "P-Implicit"]
                Explicit, Implicit, PImplicit = range(3)


            # ...

            {
                "Pressure coupling": CouplingType.Implicit,
                "attributes": {"enumNames": CouplingType.enumNames}
            }
    '''
    def __init__(self):
        self.properties = []

    def getProperties(self):
        '''
        Get an accessor proxy class that allows to query the properties simply by name.
        To access a property with a particular name, e.g., ``'Number of time steps'``, use::
        
            getProperties()['Number of time steps'] 
            
        If the property name is not unique, e.g., there is
        a ``'Number of time steps'`` property in property groups ``'Run 1'`` and ``'Run 2'``, use::
        
            getProperties()['Run 2']['Number of time steps']
            
        to disambiguate the access.
        '''
        return PropertyAccessor(self.properties)