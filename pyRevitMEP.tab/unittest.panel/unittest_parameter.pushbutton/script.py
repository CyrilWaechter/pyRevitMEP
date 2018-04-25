# coding: utf8
import unittest

from System import Guid

from Autodesk.Revit.DB import ParameterType

from pypevitmep.parameter import SharedParameter


class TestSharedParameter(unittest.TestCase):

    def test_create_shared_parameter(self):
        shared_parameter = SharedParameter("TêstName", "Text", "TêstGroup", None, "Têst description", True, True, True)
        self.assertEqual(shared_parameter.name, "TêstName")
        self.assertEqual(shared_parameter.type, ParameterType.Text)
        self.assertEqual(SharedParameter.group, "TêstGroup")
        self.assertIsInstance(shared_parameter.guid, Guid)
        self.assertEqual(shared_parameter.description, "Têst description")
        self.assertTrue(shared_parameter.new)
        self.assertTrue(shared_parameter.visible)
        self.assertTrue(shared_parameter.modifiable)


if __name__ == "__main__":
    unittest.main()
