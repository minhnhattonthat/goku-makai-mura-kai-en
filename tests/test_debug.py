"""Warp tool logic that needs no emulator."""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "debug"))

import scenes


class FakeSession:
    def __init__(self): self.mem = {}
    def wr(self, a, data): self.mem[a] = bytes(data)
    def w32(self, a, v): self.mem[a] = struct.pack("<I", v & 0xffffffff)


class FakeGame:
    def __init__(self): self.s = FakeSession()


def test_point_string_wraps_offset_back_to_scratch():
    # the getter does base + offset in 32 bits, so a scratch address below the file needs a wrapped offset
    d = struct.pack("<3I", 2, 12, 15) + b"ab\0" + b"cde\0"
    g, addr = FakeGame(), 0x09000000
    scenes.point_string(g, addr, 11, d, 1)
    slot = struct.unpack("<I", g.s.mem[addr + 4 + 11 * 4])[0]
    assert (addr + slot) & 0xffffffff == 0x08801000
    assert g.s.mem[0x08801000].startswith(b"cde\0")


def test_read_sites_are_lw_a1_at_the_stage_fields():
    for a in scenes.ADDR.values():
        assert a["stage_read_orig"] == 0x8e650000 | a["stage_off"]
        assert a["area_read_orig"] == 0x8e650000 | (a["stage_off"] + 4)


def test_both_games_have_the_same_scene_names():
    assert set(scenes.SCENES["go"]) - {"sub_all"} == set(scenes.SCENES["re"])


def test_stage_list_has_every_area_once():
    assert len(scenes.STAGES) == len(set(scenes.STAGES)) == 26
