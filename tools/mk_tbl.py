"""mk_tbl.py: build tbl/jp.tbl (byte code -> character) from jfont_00.bft plus the glyph rows read off the font sheet.

Code -> glyph comes from the .bft (docs/re/text.md); glyph -> character is ROWS, read by eye (kanji confirmed by the script
reading as sentences). Cells past the bottom of the 512x512 sheet have no glyph and get no entry.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NO = "�"  # a cell with no character
ROWS = [
    NO + "0123456789ABCDEFGHIJKLMNOPQ",
    "RSTUVWXYZabcdefghijklmnopqrs",
    "tuvwxyz-:!?()',;/*+=.&#%\"" + NO + "▼★",
    NO + "あいうえおかきくけこさしすせそたちつてとなにぬねのはひ",
    "ふへほまみむめもやゆよらりるれろわをんがぎぐげござじずぜ",
    "ぞだぢづでどばびぶべぼぱぴぷぺぽぁぃぅぇぉっゃゅょ",
    NO + "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒ",
    "フヘホマミムメモヤユヨラリルレロワヲンガギグゲゴザジズゼ",
    "ゾダヂヅデドバビブベボパピプペポァィゥェォッャュョヴ",
    "ー”“→←…〜「」『』、。・々○△□×Ⅿ∞™Ⓚ®",  # Ⅿ = the MB cell, Ⓚ = the KB cell
    "暗以異移印羽永炎押王屋下化何火解回開鎧殻確割活鎌間規騎久",
    "強玉銀空形系撃欠血剣見限光杭行高黒骨今根魂差最作散使士始",
    "子止持時失取手種収終集出駿盾所書女除晶消上場常情状侵新人",
    "水成石接選全装足速続存損墜耐態大択脱短端弾地中跳通低停敵",
    "天電動得入認覇波破馬敗爆箱発抜汎番費飛備必瓶不部封復閉変",
    "片保報宝方魔無目門矢薬容用葉要来竜了両量力棘",
    "武直追普料姫百点法的放病摘定分平老着和池甦遅置墓返良鳥類",
    "町連調物伝燃範戻般能面落扉年句由勇誘倍配妖犯反八与防頭尾",
    "立同度冒投討当内毒秘利滅離道本又特極近距魚具喰金駆詰朽軌",
    "輝去巨究牛護効個後合国向攻険験決兼現言元減黄音右応果花可",
    "家威一悪囲飲隠茨引貫危漢甘寄起器基怪界画壊各角皆外込生聖",
    "正清設説青赤進靭心身整棲数世打対村多段値待違前善先泉息揃",
    "操草自実次治邪守射者材罪左在死事財姿傷勝緒助触信小昇樹周",
    "受呪順初襲宿負線転増救脅日訪再支遥司題加望遠居継問名知項",
    "奪野未掛阻流凌乗我狙走城幾機率削絶塵弱早探会試示×研完美",
    "倒検際",
]


# bytes 00-08 are control codes in the text stream, not glyphs (docs/re/text.md); names stay hex until their meaning is proven.
# {n} is the newline: script/ files show it as a real "\n" (tools/script.py).
CTRL = {b"\x00": "{end}", b"\x01": "{n}", b"\x02": "{02}", b"\x03": "{03}", b"\x04": "{04}", b"\x05": "{05}", b"\x06": "{06}",
        b"\x07": "{c:1}", b"\x08": "{08}"}


def build(bft):
    d = Path(bft).read_bytes()
    out = dict(CTRL)
    for k, o in enumerate([0x2c] + list(struct.unpack_from("<8I", d, 0x0c))):
        for i in range(128 if k == 0 else 256):
            _, x, y, w, h = struct.unpack_from("<5H", d, o + i * 10)
            r, c = y // 16, x // 18
            if not h or r >= len(ROWS) or c >= len(ROWS[r]):
                continue
            code = bytes([i]) if k == 0 else bytes([0x7f + k, i])
            # blank cells are the spaces: half width as one byte, full width as two
            ch = ROWS[r][c] if ROWS[r][c] != NO else (" " if k == 0 else "　")
            out.setdefault(code, ch)
    return out


if __name__ == "__main__":
    t = build(sys.argv[1] if len(sys.argv) > 1 else ROOT / "work/re/font/jfont_00.bft")
    (ROOT / "tbl").mkdir(exist_ok=True)
    # several codes share a cell (digits 09-12 and 71-7A, three × cells): the first line wins on encode (tbl.py), so the
    # codes the script uses go first; any other alias decodes as [XX] bytes and still roundtrips
    prefer = {bytes([c]) for c in range(0x71, 0x7b)} | {b"\x82\xa8"}
    order = sorted(t.items(), key=lambda kv: (kv[0] not in prefer, len(kv[0]), kv[0]))
    (ROOT / "tbl/jp.tbl").write_text("".join(f"{k.hex().upper()}={v if v != ' ' else chr(92) + 's'}\n" for k, v in order), encoding="utf-8", newline="\n")
    print(len(t), "codes")
