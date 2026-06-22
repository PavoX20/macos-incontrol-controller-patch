import unittest

import patch


class ControllerNamePatchTests(unittest.TestCase):
    def test_physical_playstation_names_fit_in_profile_replacements(self):
        playstation_patches = getattr(patch, "PLAYSTATION_PHYSICAL_PATCHES", [])
        replacements = dict(playstation_patches)

        self.assertIn("Sony Computer Entertainment Wireless Controller", replacements)
        self.assertIn("Sony Interactive Entertainment Wireless Controller", replacements)
        self.assertEqual(
            replacements["Sony Computer Entertainment Wireless Controller"],
            "DualSense Wireless Controller",
        )
        self.assertEqual(
            replacements["Sony Interactive Entertainment Wireless Controller"],
            "Control Viejo Pablo",
        )

        for old_name, new_name in playstation_patches:
            self.assertLessEqual(len(new_name), len(old_name))

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
