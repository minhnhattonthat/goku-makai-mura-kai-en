"""survey_text.py DIR: recon scan. Finds Shift-JIS / UTF-8 / UTF-16LE Japanese sentences in every extracted file.

Only long kana-bearing runs count, so binary noise stays out. Prints one line per hit, then per-extension totals.
"""
import collections
import os
import re
import sys

KANA = re.compile("[ぁ-ゖァ-ヺー]")
SKIP = (".at3", ".pbd", ".phd", ".gmo", ".pmf", ".png")
SJIS = re.compile(rb"(?:[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc]|[\x20-\x7e]){4,}")
U16 = re.compile(rb"(?:[\x00-\xff][\x30\x4e-\x9f\xff]){3,}")
U8 = re.compile(rb"(?:[\xe3-\xe9][\x80-\xbf]{2}|[\x20-\x7e]){3,}")


def hits(b):
    for rx, enc in ((SJIS, "cp932"), (U8, "utf-8"), (U16, "utf-16le")):
        for m in rx.finditer(b):
            try:
                s = m.group().decode(enc)
            except UnicodeDecodeError:
                continue
            if len(KANA.findall(s)) >= 3:
                yield enc, m.start(), s


def main(root):
    tot = collections.Counter()
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.lower().endswith(SKIP):
                continue
            p = os.path.join(dp, f)
            b = open(p, "rb").read()
            for enc, off, s in hits(b):
                tot[os.path.splitext(f)[1]] += 1
                print(f"{p}:{off:#x} {enc} {s!r}")
    print(tot, file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1])
