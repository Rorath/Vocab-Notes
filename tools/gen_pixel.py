"""Generate the home-page endless-runner pixel sprites from ASCII maps.

Each sprite is authored as an ASCII grid ('#' = a filled pixel). Runs of '#'
in a row are merged into <rect>s and emitted as a crisp-edges SVG, so the art
scales up sharply. Dino and bird are two-frame sprite sheets (frames placed
side by side) that the CSS plays via `background-position-x` + `steps(2)`.

Run with the project's venv python:  python tools/gen_pixel.py
Output: static/pixel/*.svg
"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "static", "pixel")
os.makedirs(OUT, exist_ok=True)


def to_svg(frames, color):
    """frames: list of equal-height ascii maps ('#'=pixel). Placed side by side."""
    h = len(frames[0])
    rects, xoff = [], 0
    for f in frames:
        w = len(f[0])
        for y, row in enumerate(f):
            x = 0
            while x < len(row):
                if row[x] == '#':
                    x2 = x
                    while x2 < len(row) and row[x2] == '#':
                        x2 += 1
                    rects.append((xoff + x, y, x2 - x))
                    x = x2
                else:
                    x += 1
        xoff += w
    W = xoff
    body = "".join(f'<rect x="{x}" y="{y}" width="{w}" height="1"/>' for x, y, w in rects)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
            f'viewBox="0 0 {W} {h}" shape-rendering="crispEdges" fill="{color}">{body}</svg>')


# ---- dino (16x16), head faces right; two run frames differ only in the feet ----
dino_body = [
    "........#####...",
    "........######..",
    "........#.####..",
    "........######..",
    "........#####...",
    "#.......#####...",
    "##.....######...",
    "###..########...",
    ".###########....",
    "..##########....",
    "..#########.....",
    "..########......",
    "..##...###......",
    "..##....##......",
]
dino_f1 = dino_body + ["..#.....##......", "..#.....##......"]
dino_f2 = dino_body + ["..##....#.......", "..##....##......"]

# ---- cactus small (7x11) and large (9x14) ----
cactus_s = [
    "...#...", "...#...", ".#.#...", ".#.#.#.", ".###.#.",
    "...###.", "...#...", "...#...", "...#...", "...#...", "...#...",
]
cactus_l = [
    "....#....", "....#....", ".#..#....", ".#..#..#.", ".#..#..#.",
    ".####..#.", "....####.", "....#....", "....#....", "....#....",
    "....#....", "....#....", "....#....", "....#....",
]

# ---- cloud (12x5) ----
cloud = [
    "...####.....",
    ".########...",
    "############",
    ".##########.",
    "...######...",
]

# ---- bird (11x7), two flap frames ----
bird_up = [
    "#.........#",
    ".#.......#.",
    "..#.....#..",
    "..#######..",
    "...#####...",
    "....###....",
    "...........",
]
bird_down = [
    "...........",
    "...#####...",
    "..#######..",
    "..#.....#..",
    ".#.......#.",
    "#.........#",
    "...........",
]

files = {
    "dino.svg":     to_svg([dino_f1, dino_f2], "#eef1f7"),
    "cactus_s.svg": to_svg([cactus_s], "#3ce0d0"),
    "cactus_l.svg": to_svg([cactus_l], "#3ce0d0"),
    "cloud.svg":    to_svg([cloud], "#c9d2ff"),
    "bird.svg":     to_svg([bird_up, bird_down], "#c084fc"),
}
for name, data in files.items():
    with open(os.path.join(OUT, name), "w") as fh:
        fh.write(data)
    print(f"wrote {name} ({len(data)} bytes)")
