import PythonQtMock as PythonQt
import sys

sys.modules['PythonQt'] = PythonQt

import unittest
from CRIMSONCore.PropertyStorage import PropertyStorage


class TestPropertyStorage(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.storage = PropertyStorage()
        cls.storage.properties = [
            {"name": 'a',
             "value": [
                 {"name": 'b',
                  "value": 1}
                ]
             }]

    @classmethod
    def tearDown(cls):
        del(cls.storage)

    def testAccess(self):
        storage = TestPropertyStorage.storage

        self.assertEqual(storage.getProperties()['b'], 1)
        self.assertEqual(storage.getProperties()['a']['b'], 1)

        storage.getProperties()['b'] = 2
        self.assertEqual(storage.getProperties()['b'], 2)

        with self.assertRaises(KeyError):
            storage.getProperties()['unknown']

        with self.assertRaises(TypeError):
            storage.getProperties()['b'] = 1.0
