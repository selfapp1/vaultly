"""アプリアイコン(PNG)を外部ライブラリなしで生成するスクリプト。
グラデーション背景 + 白い南京錠のシンプルなアイコンを描画する。
"""
import struct
import zlib
import math
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "icons")
os.makedirs(OUT_DIR, exist_ok=True)

# グラデーション色 (indigo -> violet)
C1 = (79, 70, 229)   # #4f46e5
C2 = (139, 92, 246)  # #8b5cf6


def lerp(a, b, t):
    return a + (b - a) * t


def bg_color(x, y, size):
    t = (x + y) / (2 * size)
    r = lerp(C1[0], C2[0], t)
    g = lerp(C1[1], C2[1], t)
    b = lerp(C1[2], C2[2], t)
    return r, g, b


def rounded_square_mask(x, y, size, radius):
    # 角丸四角形の内側かどうか
    cx = min(max(x, radius), size - radius)
    cy = min(max(y, radius), size - radius)
    dx, dy = x - cx, y - cy
    return (dx * dx + dy * dy) <= radius * radius


def padlock_mask(x, y, size):
    # 中心基準の正規化座標 (-1..1)
    nx = (x - size / 2) / (size / 2)
    ny = (y - size / 2) / (size / 2)

    body = False
    shackle = False

    # 本体(角丸四角形): 縦0.05〜0.55、横 -0.32〜0.32
    if -0.34 <= nx <= 0.34 and -0.02 <= ny <= 0.56:
        # 角丸処理(簡易)
        r = 0.08
        left, right = -0.34, 0.34
        top, bottom = -0.02, 0.56
        cx = min(max(nx, left + r), right - r)
        cy = min(max(ny, top + r), bottom - r)
        dx, dy = nx - cx, ny - cy
        if dx * dx + dy * dy <= r * r:
            body = True

    # つる(シャックル): 半円リング
    ring_cx, ring_cy = 0.0, -0.05
    outer_r = 0.30
    inner_r = 0.18
    dx, dy = nx - ring_cx, ny - ring_cy
    dist = math.sqrt(dx * dx + dy * dy)
    if inner_r <= dist <= outer_r and dy <= 0.02:
        shackle = True

    # 鍵穴
    keyhole = False
    khx, khy = nx, ny - 0.24
    if khx * khx / (0.045 ** 2) + khy * khy / (0.06 ** 2) <= 1:
        keyhole = True
    if abs(khx) < 0.025 and 0.24 <= (ny - 0.24 + 0.02) <= 0.13 and ny > 0.24:
        pass

    return body or shackle, keyhole


def make_png(size, path):
    rows = []
    radius = size * 0.22
    for y in range(size):
        row = bytearray()
        row.append(0)  # フィルタタイプ: None
        for x in range(size):
            if not rounded_square_mask(x, y, size, radius):
                row += bytes((0, 0, 0, 0))
                continue
            r, g, b = bg_color(x, y, size)
            lock, keyhole = padlock_mask(x, y, size)
            if lock:
                if keyhole:
                    row += bytes((int(r), int(g), int(b), 255))
                else:
                    row += bytes((255, 255, 255, 255))
            else:
                row += bytes((int(r), int(g), int(b), 255))
        rows.append(bytes(row))

    raw = b"".join(rows)

    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw, 9)
    png = sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")

    with open(path, "wb") as f:
        f.write(png)
    print(f"wrote {path} ({size}x{size})")


for size, name in [(180, "icon-180.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
    make_png(size, os.path.join(OUT_DIR, name))
