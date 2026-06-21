import unittest

import patch


class DirectInputAssignmentPatchTests(unittest.TestCase):
    def test_order_joysticks_by_index_keeps_duplicate_names_in_separate_slots(self):
        names = ["Microsoft GamePad-1", "Microsoft GamePad-1"]

        ordered = patch.order_joysticks_by_index(names, slot_count=4)

        self.assertEqual(
            ordered,
            ["Microsoft GamePad-1", "Microsoft GamePad-1", "", ""],
        )

    def test_directinput_assignment_patch_replaces_original_body(self):
        data = bytearray(
            b"prefix"
            + patch.DIRECTINPUT_UPDATE_ASSIGNED_JOYSTICKS_ORIGINAL_BODY
            + b"suffix"
        )

        self.assertTrue(patch.patch_directinput_assignment(data))

        self.assertIn(patch.DIRECTINPUT_UPDATE_ASSIGNED_JOYSTICKS_PATCHED_BODY, data)
        self.assertNotIn(patch.DIRECTINPUT_UPDATE_ASSIGNED_JOYSTICKS_ORIGINAL_BODY, data)

    def test_directinput_assignment_patch_is_idempotent(self):
        data = bytearray(
            b"prefix"
            + patch.DIRECTINPUT_UPDATE_ASSIGNED_JOYSTICKS_PATCHED_BODY
            + b"suffix"
        )
        before = bytes(data)

        self.assertTrue(patch.patch_directinput_assignment(data))

        self.assertEqual(bytes(data), before)


if __name__ == "__main__":
    unittest.main()
