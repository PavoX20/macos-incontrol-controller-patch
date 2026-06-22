#!/usr/bin/env python3
"""
Steam Input Controller Patch for InControl Games

Patches Assembly-CSharp.dll to recognize Steam Input's virtual controllers
("Microsoft GamePad-1", "Microsoft GamePad-2", etc.) as Xbox 360 controllers.

Supported games: Tricky Towers, Overcooked! 2

Usage:
    python3 patch.py [--restore] [path/to/Assembly-CSharp.dll]
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

STEAM_LIBRARY_PATH = Path.home() / "Library/Application Support/Steam/steamapps/common"
DLL_RELATIVE_PATH = Path("Contents/Resources/Data/Managed/Assembly-CSharp.dll")

GAMES: List[Tuple[str, Path]] = [
    ("Tricky Towers", STEAM_LIBRARY_PATH / "Tricky Towers" / "TrickyTowers.app" / DLL_RELATIVE_PATH),
    ("Overcooked! 2", STEAM_LIBRARY_PATH / "Overcooked! 2" / "Overcooked2.app" / DLL_RELATIVE_PATH),
]

PATCHES: List[Tuple[str, str]] = [
    ("Microsoft Wireless 360 Controller", "Microsoft GamePad-1"),
    ("Mad Catz, Inc. Mad Catz FPS Pro GamePad", "Microsoft GamePad-2"),
    ("Mad Catz, Inc. MadCatz Call of Duty GamePad", "Microsoft GamePad-3"),
    ("\xa9Microsoft Corporation Controller", "Microsoft GamePad-4"),
]

DIRECTINPUT_UPDATE_ASSIGNED_JOYSTICKS_ORIGINAL_BODY = bytes.fromhex(
    "133004003b010000a9010011289505000a0a06392e010000160b386c000000"
    "7ef8060004079a3a110000007ef8060004077ee300000aa2384b000000160c"
    "160d382700000006099a391b00000006099a7ef8060004079a6f8101000a"
    "3907000000170c380d0000000917580d09068e693fd0ffffff083a0c000000"
    "7ef8060004077ee300000aa20717580b077ef80600048e693f87ffffff161304"
    "389c0000000611049a3a0500000038880000001613051613063824000000"
    "7ef806000411069a0611049a6f8101000a39080000001713053814000000"
    "11061758130611067ef80600048e693fceffffff11053a44000000161307382e"
    "0000007ef806000411079a7ee300000a6f8101000a39110000007ef8060004"
    "11070611049aa2381400000011071758130711077ef80600048e693fc4ffffff"
    "1104175813041104068e693f5affffff2a"
)

DIRECTINPUT_UPDATE_ASSIGNED_JOYSTICKS_PATCHED_BODY = bytes.fromhex(
    "133004003b010000a9010011289505000a0a062d012a160b2b2907068e693202"
    "2b0506079a2d0e7ef8060004077ee300000aa22b0a7ef80600040706079aa2"
    "0717580b077ef80600048e6932cd2a"
    + ("00" * (len(DIRECTINPUT_UPDATE_ASSIGNED_JOYSTICKS_ORIGINAL_BODY) - 78))
)


def order_joysticks_by_index(joystick_names: List[str], slot_count: int) -> List[str]:
    """Return joystick slots keyed by Unity joystick index, preserving duplicate names."""
    ordered = [""] * slot_count
    for index, joystick_name in enumerate(joystick_names[:slot_count]):
        ordered[index] = joystick_name or ""
    return ordered


def patch_directinput_assignment(data: bytearray) -> bool:
    """DirectInput IL patch is disabled; Unity 2017 Mono rejects the rewritten body."""
    return False


def patch_string(data: bytearray, old_str: str, new_str: str) -> bool:
    """Replace a .NET User String in the DLL."""
    old_utf16 = old_str.encode("utf-16-le")
    new_utf16 = new_str.encode("utf-16-le")

    if len(new_utf16) > len(old_utf16):
        log.error("'%s' is longer than '%s'", new_str, old_str)
        return False

    old_length_byte = len(old_utf16) + 1
    new_length_byte = len(new_utf16) + 1

    pattern = bytes([old_length_byte]) + old_utf16
    pos = data.find(pattern)

    if pos == -1:
        new_pattern = bytes([new_length_byte]) + new_utf16
        if new_pattern in data:
            log.info("  Already patched: '%s'", new_str)
            return True
        return False

    data[pos] = new_length_byte
    data[pos + 1:pos + 1 + len(new_utf16)] = new_utf16
    for i in range(len(new_utf16), len(old_utf16) + 1):
        data[pos + 1 + i] = 0x00

    log.info("  Patched: '%s' -> '%s'", old_str, new_str)
    return True


def patch_dll(dll_path: Path) -> bool:
    backup = dll_path.with_suffix(".dll.bak")

    if not dll_path.exists():
        log.error("DLL not found: %s", dll_path)
        return False

    try:
        if not backup.exists():
            shutil.copy2(dll_path, backup)
            log.info("Backup: %s", backup.name)

        data = bytearray(dll_path.read_bytes())

        patched = sum(1 for old, new in PATCHES if patch_string(data, old, new))
        directinput_patched = False

        if patched == 0 and not directinput_patched:
            log.error("No strings found to patch")
            return False

        dll_path.write_bytes(data)
        log.info("Patched %d/%d controller names", patched, len(PATCHES))
        return True

    except PermissionError:
        log.error("Permission denied: Unable to read/write to %s. Try checking folder permissions.", dll_path.name)
        return False
    except Exception as e:
        log.error("An unexpected error occurred while patching: %s", str(e))
        return False


def restore_dll(dll_path: Path) -> bool:
    backup = dll_path.with_suffix(".dll.bak")
    if not backup.exists():
        log.error("No backup found for %s", dll_path.name)
        return False

    try:
        shutil.copy2(backup, dll_path)
        log.info("Restored from backup successfully")
        return True
    except PermissionError:
        log.error("Permission denied: Unable to restore file %s", dll_path.name)
        return False


def find_installed_games() -> List[Tuple[str, Path]]:
    """Return list of (name, dll_path) for games that are installed."""
    return [(name, dll_path) for name, dll_path in GAMES if dll_path.exists()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Steam Input Controller Patch for InControl Games")
    parser.add_argument("custom_path", nargs="?", type=Path, help="Optional specific path to Assembly-CSharp.dll")
    parser.add_argument("--restore", action="store_true", help="Restore the DLL from backup")

    args = parser.parse_args()

    process_game = restore_dll if args.restore else patch_dll

    if args.custom_path:
        games_to_process = [("", args.custom_path)]
    else:
        games_to_process = find_installed_games()

    if not games_to_process:
        log.error("No supported games found automatically. Provide a direct path to Assembly-CSharp.dll.")
        return 1

    all_succeeded = True
    for game_name, dll_path in games_to_process:
        if game_name:
            log.info("\n%s", game_name)
        log.info("DLL: %s", dll_path)

        if not process_game(dll_path):
            all_succeeded = False

    if all_succeeded and not args.restore:
        log.info("\nSuccess! Now enable Steam Input in each game's Steam properties.")

    return 0 if all_succeeded else 1


if __name__ == "__main__":
    sys.exit(main())
