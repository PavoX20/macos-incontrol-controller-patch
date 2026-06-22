import unittest

import patch


class ControllerNamePatchTests(unittest.TestCase):
    def test_patch_dll_leaves_directinput_method_body_unchanged(self):
        data = bytearray(
            b"prefix"
            + patch.DIRECTINPUT_UPDATE_ASSIGNED_JOYSTICKS_ORIGINAL_BODY
            + b"suffix"
        )
        before = bytes(data)

        self.assertFalse(patch.patch_directinput_assignment(data))

        self.assertEqual(bytes(data), before)


if __name__ == "__main__":
    unittest.main()
