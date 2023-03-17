import unittest
import sys
sys.path.append('../APP')
import scancode_to_hid_code

class TestEnumList(unittest.TestCase):

    def test_enum_equality(self):
        # Ensure objects in enum class and list are equal and refer to same object
        key_a = next(filter(lambda x: x.name == "A", scancode_to_hid_code.SCANCODE_LIST), None)
        self.assertEqual(key_a, scancode_to_hid_code.ScanCodeList.KEY_A.value)
        self.assertTrue(key_a is scancode_to_hid_code.ScanCodeList.KEY_A.value)

    def test_enum_type(self):
        # Ensure all members of ScanCodeList are of type ScanCode
        self.assertTrue(isinstance(member.value, scancode_to_hid_code.ScanCode) for member in scancode_to_hid_code.ScanCodeList)


if __name__ == "__main__":
    unittest.main(verbosity=2)