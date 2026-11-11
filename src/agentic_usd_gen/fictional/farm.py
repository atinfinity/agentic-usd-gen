"""Fictional designs for a plant factory (an artificial-light strawberry vertical farm): a growing rack with and
without plants, a strawberry plant in a nursery pot and a magnetic guide tape for AGVs.

No real product names, brands or logos; shapes and sizes are typical values, not any real farm's. Front is -Y
(the aisle side of the rack, where the fruit hangs over the trough edge).
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import Product
from .hc_garden import SOIL, _p, _seg, _soil_top
from .paint import Canvas, finish, mix
from .products import _face, _lamp

WHITE = "#FFFFFF"
PIPE = "#EEEEEA"  # white painted steel pipe
TROUGH = "#F3F3EF"
LED_BODY = "#DADCDE"
TUBE = "#202020"
LEAF, LEAF_DARK, LEAF_LIGHT = "#3F7F2F", "#2B5E22", "#5C9A3E"
RIPE, TURNING = "#C8102E", "#E9774A"
CALYX = "#4E8A30"
POT = "#1E1E1E"

LEAF_KW = dict(finish_="matte", material="leaf_grass", collision=False)


# ---------------------------------------------------------------- textures


# leaf tones (images 0-3): mature, dark, young (the folded centre leaf) and old (yellowing outer leaves)
LEAF_TONES = ("#3F7F2F", "#2B5E22", "#6FA84A", "#8E9A3C")
_TONE_SHADES = (("#4E8E38", "#2F6A25"), ("#3A7029", "#1F4A18"), ("#86BC5C", "#5C9A3E"), ("#94A040", "#66782C"))
# fruit stages (images 4-7): the part color is the average, the texture runs from the tip to the shoulders
STAGES = ("red", "turning", "white", "green")
BERRY_COLOR = {"red": RIPE, "turning": TURNING, "white": "#EEEAD2", "green": "#A8C766"}
BERRY_LEN = {"red": 0.040, "turning": 0.037, "white": 0.032, "green": 0.024}  # fruit length [m] at scale 1
_BERRY_SHADES = {  # (tip, middle, shoulder)
    "red": ("#B30E24", "#C8102E", "#A80F22"),
    "turning": ("#C9272C", "#EC8650", "#F1E6C4"),
    "white": ("#F3E3D0", "#F2EEDA", "#DCE8B8"),
    "green": ("#C2D98A", "#A8C766", "#8DB552"),
}
FLOWER_IMG = 8


def _leaflet(tone: int, seed: int, px: float = 6.0) -> np.ndarray:
    """One leaflet seen from above, base on the left and tip on the right (the leaf part's outline crops it): an
    even green with a pale midrib and pairs of impressed side veins running forward to the teeth."""
    light, dark = _TONE_SHADES[tone]
    c = Canvas(90, 60, px, dark, seed)
    c.gradient(0, 0, 90, 60, light, dark, horizontal=True)
    rng = c.rng
    for _ in range(60):  # a mottled surface between the veins
        x, y, r = rng.uniform(0, 90), rng.uniform(0, 60), rng.uniform(2, 6)
        c.ellipse(x - r, y - r * 0.6, x + r, y + r * 0.6, fill=mix(light if rng.random() < 0.5 else dark, LEAF, 0.5))
    if tone == 3:  # old leaves: brown spots and a yellowing tip
        for _ in range(8):
            x, y, r = rng.uniform(20, 88), rng.uniform(8, 52), rng.uniform(1.0, 2.5)
            c.ellipse(x - r, y - r, x + r, y + r, fill="#7A5A2A")
    vein, hi = mix(dark, "#000000", 0.3), mix(light, WHITE, 0.25)
    for i in range(10):
        x0 = 5 + i * 8.0
        for side in (-1, 1):
            t = min((x0 + 14) / 90, 0.99)
            hw = 30 * (t ** 0.75 * (1 - t) ** 0.35) / 0.4956
            pts = [(x0, 30), (x0 + 7, 30 + side * hw * 0.55), (x0 + 14, 30 + side * hw * 0.98)]
            c.line(pts, vein, 0.8)
            c.line([(x + 0.6, y - side * 0.5) for x, y in pts], hi, 0.35)
    c.line([(0, 30), (90, 30)], mix(light, WHITE, 0.3), 1.2)
    c.line([(0, 30.9), (90, 30.9)], vein, 0.4)
    return finish(c.array(), "paper", seed, 0.25)


def _berry_skin(stage: str, seed: int, px: float = 8.0) -> np.ndarray:
    """A fruit's skin for the fruit part (the centre is the tip, the edge the shoulders under the calyx): the
    stage's colors from the tip up (strawberries color from the tip) and seeds sunk in pits."""
    tip, mid, top = _BERRY_SHADES[stage]
    c = Canvas(60, 60, px, "#200000", seed)  # the corners are never shown; dark so the image is not trimmed
    for k in range(48):
        f = 1 - k / 48
        col = mix(tip, mid, f / 0.55) if f < 0.55 else mix(mid, top, (f - 0.55) / 0.45)
        r = 30 * f
        c.ellipse(30 - r, 30 - r, 30 + r, 30 + r, fill=col)
    seed_col = {"red": "#E9C24A", "turning": "#E3C34A", "white": "#E2D48C", "green": "#D1D58A"}[stage]
    rng = c.rng
    for i in range(16):
        for j in range(16):
            x = 1 + j * 3.9 + (1.95 if i % 2 else 0) + rng.uniform(-0.5, 0.5)
            y = 1 + i * 3.6 + rng.uniform(-0.5, 0.5)
            r = math.hypot(x - 30, y - 30)
            if r > 27.5 or r < 1.5:
                continue
            f = r / 30
            here = mix(tip, mid, f / 0.55) if f < 0.55 else mix(mid, top, (f - 0.55) / 0.45)
            c.ellipse(x - 1.1, y - 0.9, x + 1.1, y + 0.9, fill=mix(here, "#000000", 0.28))
            c.ellipse(x - 0.55, y - 0.75, x + 0.55, y + 0.45, fill=seed_col)
    return finish(c.array(), "paper", seed, 0.2)


def _flower_face(seed: int) -> np.ndarray:
    """A strawberry flower from the front for the star part (petal tips at 0, ±72 and ±144 degrees): five white
    petals with faint veins and a green-yellow centre ringed with stamens."""
    c = Canvas(30, 30, 16, "#1E3A12", seed)
    c.ellipse(0, 0, 30, 30, fill="#FBFBF6")
    for k in range(5):  # the gaps between the petals
        a = math.radians(36 + 72 * k)
        c.line([(15 + 5.5 * math.cos(a), 15 + 5.5 * math.sin(a)), (15 + 15 * math.cos(a), 15 + 15 * math.sin(a))],
               "#D8D8CE", 0.5)
    for k in range(40):  # petal veins
        a = math.radians(k * 9 + c.rng.uniform(-2, 2))
        c.line([(15 + 5 * math.cos(a), 15 + 5 * math.sin(a)), (15 + 13 * math.cos(a), 15 + 13 * math.sin(a))],
               "#ECECE4", 0.25)
    c.ellipse(10.2, 10.2, 19.8, 19.8, fill="#E2C42A")
    c.ellipse(11.8, 11.8, 18.2, 18.2, fill="#C9CC4A")
    for _ in range(60):  # pistils on the centre
        a, r = c.rng.uniform(0, 2 * math.pi), c.rng.uniform(0, 2.8)
        x, y = 15 + r * math.cos(a), 15 + r * math.sin(a)
        c.ellipse(x - 0.35, y - 0.35, x + 0.35, y + 0.35, fill="#A9B83A")
    for k in range(24):  # stamens
        a = math.radians(k * 15 + c.rng.uniform(-4, 4))
        x, y = 15 + 4.9 * math.cos(a), 15 + 4.9 * math.sin(a)
        c.ellipse(x - 0.6, y - 0.6, x + 0.6, y + 0.6, fill="#C49A12")
    return c.array()


def _plant_images(seed: int, leaf_px: float = 6.0) -> list[np.ndarray]:
    """Images 0-3 leaflet tones, 4-7 fruit stages (STAGES), 8 flower."""
    return ([_leaflet(t, seed + t, leaf_px) for t in range(4)] + [_berry_skin(st, seed + 4 + k) for k, st in enumerate(STAGES)]
            + [_flower_face(seed + 8)])


def _trough_top(length_mm: float, width_mm: float, holes_mm: list[float], seed: int) -> np.ndarray:
    """The trough's cover from above (left of the image = -X, bottom = front): planting holes in a row, the
    medium (dark coir) showing in each, and the drip tube's dripper marks."""
    c = Canvas(length_mm, width_mm, 2, TROUGH, seed)
    c.gradient(0, 0, length_mm, width_mm, "#F6F6F2", "#E9E9E4")
    yc = width_mm / 2
    for x in holes_mm:
        c.ellipse(x - 42, yc - 42, x + 42, yc + 42, fill="#CFCFC9")
        c.ellipse(x - 38, yc - 38, x + 38, yc + 38, fill="#4A3426")
        for _ in range(30):
            a, r = c.rng.uniform(0, 2 * math.pi), c.rng.uniform(0, 34)
            px, py = x + r * math.cos(a), yc + r * math.sin(a)
            c.ellipse(px - 2, py - 1, px + 2, py + 1, fill=c.rng.choice(["#6B4B34", "#33231A", "#8A6A4A"]))
    for k in range(int(length_mm // 600) + 1):  # joints of the cover sheet
        c.line([(k * 600 + 5, 0), (k * 600 + 5, width_mm)], "#DADAD4", 1.0)
    return finish(c.array(), "paper", seed, 0.3)


def _side(length_mm: float, h_mm: float, seed: int, color: str = TROUGH) -> np.ndarray:
    c = Canvas(length_mm, h_mm, 2, color, seed)
    c.gradient(0, 0, length_mm, h_mm, mix(color, WHITE, 0.3), mix(color, "#000000", 0.06))
    c.line([(0, 6), (length_mm, 6)], mix(color, "#000000", 0.08), 1.2)  # the cover's lip
    return _face(c.array(), "paper", seed, 0.3, 4)


# ---------------------------------------------------------------- a plant (parts only)

PETIOLE, STALK, RUNNER = "#5E8A3A", "#6E9440", "#8A5A3A"
# level of detail: leaf teeth per side, tube sides, points along a stalk, fruit sides, calyx/flower segments
LITE = dict(teeth=4, tube=4, path=5, fruit=10, star=8, calyx_lobes=6)  # a rack carries 30 plants
FULL = dict(teeth=8, tube=6, path=9, fruit=24, star=48, calyx_lobes=10)  # a single pot seen up close


def _bez(p0, c, p1, n: int) -> np.ndarray:
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * np.asarray(p0, float) + 2 * (1 - t) * t * np.asarray(c, float) + t ** 2 * np.asarray(p1, float)


def _tube(name: str, pts, d0: float, d1: float, color: str, sides: int, show=None) -> Part:
    pts = np.asarray(pts, float)
    return _p(name, "tube", (d0, d1, 0.0), tuple(pts[0]), color, profile=(pts - pts[0]).round(5).tolist(),
              segments=sides, show=show, **LEAF_KW)


def _aim(v) -> tuple[float, float, float]:
    """Rotation (X then Y) turning +Z to the direction v."""
    v = np.asarray(v, float) / np.linalg.norm(v)
    return (math.degrees(math.asin(-v[1])), math.degrees(math.atan2(v[0], v[2])), 0.0)


def _leaflet_part(name: str, base, heading: float, pitch: float, length: float, tone: int, d: dict, show) -> Part:
    """A leaflet whose base is at `base`, pointing toward `heading` (degrees from +X) tilted up `pitch` degrees."""
    th, ph = math.radians(heading), math.radians(pitch)
    c = np.add(base, length / 2 * np.array([math.cos(ph) * math.cos(th), math.cos(ph) * math.sin(th), math.sin(ph)]))
    return _p(name, "leaf", (length, length * 0.68, length * 0.12), tuple(c), LEAF_TONES[tone], rot=(0.0, -pitch, heading),
              faces={"top": tone}, segments=d["teeth"], show=show, **LEAF_KW)


def _leaf(prefix: str, base, heading: float, rise: float, petiole: float, size: float, tone: int, rng, d: dict,
          show=None, blade: float | None = None, spread: float = 52.0) -> list[Part]:
    """A trifoliate leaf: a petiole rising steeply from `base` and bending out toward `heading` (`rise` degrees above
    the horizon at its tip), and three serrated leaflets at the tip held about level (`blade` degrees)."""
    th, r = math.radians(heading), math.radians(rise)
    out = np.array([math.cos(th), math.sin(th), 0.0])
    base = np.asarray(base, float)
    tip = base + petiole * (math.cos(r) * out + [0, 0, math.sin(r)])
    ctrl = base + petiole * (0.2 * out + [0, 0, 0.6])
    parts = [_tube(f"{prefix}Petiole", _bez(base, ctrl, tip, d["path"]), 0.0034, 0.0024, PETIOLE, d["tube"], show)]
    blade = rng.uniform(-6, 16) if blade is None else blade
    centre = tip + 0.006 * out
    parts.append(_leaflet_part(f"{prefix}Leaflet0", centre, heading + rng.uniform(-5, 5), blade, size, tone, d, show))
    for k, side in ((1, -1), (2, 1)):
        parts.append(_leaflet_part(f"{prefix}Leaflet{k}", tip, heading + side * (spread + rng.uniform(-8, 8)),
                                   blade - rng.uniform(2, 10), size * rng.uniform(0.82, 0.9), tone, d, show))
    return parts


def _crown(prefix: str, pos, s: float, seg: int) -> Part:
    x, y, z = pos
    return _p(f"{prefix}Crown", "dome", (0.04 * s, 0.04 * s, 0.026 * s), (x, y, z + 0.013 * s), "#5E6B2E",
              finish_="matte", material="leaf_grass", collision=False, segments=seg)


def _foliage(prefix: str, pos, rng, d: dict, s: float, n: int, lean: float = 90.0, old: int = 0, show=None,
             petiole=(0.08, 0.12), size=(0.050, 0.064), young: bool = True) -> list[Part]:
    """n leaves fanned around the crown (more toward `lean`), the outer `old` of them low and yellowing, and a
    young light green leaf standing up in the centre."""
    x, y, z = pos
    base = (x, y, z + 0.02 * s)
    parts: list[Part] = []
    for k in range(n):
        heading = lean + (k - (n - 1) / 2) * (330.0 / n) + rng.uniform(-12, 12)
        is_old = k in ({0, n - 1} if old >= 2 else {0} if old else set())
        rise = rng.uniform(16, 28) if is_old else rng.uniform(36, 62)
        tone = 3 if is_old else (1 if rng.random() < 0.4 else 0)
        parts += _leaf(f"{prefix}L{k}", base, heading, rise, rng.uniform(*petiole) * s, rng.uniform(*size) * s, tone,
                       rng, d, show, blade=rng.uniform(-22, -8) if is_old else None)
    if young:
        parts += _leaf(f"{prefix}LY", base, lean + rng.uniform(-40, 40), rng.uniform(74, 82), petiole[0] * 0.55 * s,
                       size[0] * 0.6 * s, 2, rng, d, show, blade=rng.uniform(40, 55), spread=28.0)
    return parts


def _berry(prefix: str, attach, stage: str, s: float, rng, d: dict, show=None, calyx: bool = True) -> list[Part]:
    """A fruit hanging from `attach` (the end of its pedicel): the calyx's sepals spread on the shoulders and the
    fruit (tip down) below it, tilted a little. Sizes follow the stage (green fruit are small)."""
    fl = BERRY_LEN[stage] * s * rng.uniform(0.9, 1.1)
    fw = fl * rng.uniform(0.8, 0.9)
    rot = (rng.uniform(-14, 14), rng.uniform(-14, 14), rng.uniform(0, 360))
    from ..shapes.assembly import rotation_matrix  # noqa: PLC0415 (geometry helper, not needed at import)
    R = rotation_matrix(list(rot))
    attach = np.asarray(attach, float)
    parts = [_p(f"{prefix}Fruit", "fruit", (fw, fw, fl), tuple(attach - R @ [0, 0, fl / 2]), BERRY_COLOR[stage],
                "glossy", rot=rot, faces={"top": 4 + STAGES.index(stage)}, material="food", collision=False,
                segments=d["fruit"], show=show)]
    if calyx:
        D = BERRY_LEN["red"] * s * 1.05
        hs = D * 0.08
        parts.append(_p(f"{prefix}Calyx", "star", (D, D, hs), tuple(attach + R @ [0, 0, hs / 2 + 0.0006]), CALYX,
                        rot=rot, profile=[[d["calyx_lobes"], 0.22, 2.2]], segments=d["star"], **LEAF_KW))
    return parts


def _flower(prefix: str, tip, facing, s: float, d: dict, show=None) -> list[Part]:
    """An open flower at `tip` facing `facing`: five white petals (image 8), and up close a raised yellow centre
    and green sepals behind the petals."""
    v = np.asarray(facing, float) / np.linalg.norm(facing)
    rot = _aim(v)
    D = 0.028 * s
    tip = np.asarray(tip, float)
    parts = [_p(f"{prefix}Petals", "star", (D, D, D * 0.08), tuple(tip + v * 0.0015), WHITE, rot=rot,
                profile=[[5, 0.62, 0.45]], faces={"top": FLOWER_IMG}, segments=d["star"], show=show, **LEAF_KW)]
    if d is FULL:
        parts.append(_p(f"{prefix}Centre", "dome", (0.0075 * s, 0.0075 * s, 0.003 * s), tuple(tip + v * 0.0028),
                        "#D9C430", "matte", rot=rot, collision=False, material="leaf_grass", segments=16, show=show))
        parts.append(_p(f"{prefix}Sepals", "star", (D * 0.75, D * 0.75, D * 0.06), tuple(tip + v * 0.0002), CALYX,
                        rot=rot, profile=[[10, 0.25, 2.0]], segments=d["star"], show=show, **LEAF_KW))
    return parts


def _bud(prefix: str, tip, facing, s: float, d: dict, show=None) -> Part:
    v = np.asarray(facing, float) / np.linalg.norm(facing)
    return _p(f"{prefix}Bud", "pointed_dome", (0.009 * s, 0.009 * s, 0.011 * s), tuple(np.asarray(tip) + v * 0.0055 * s),
              "#7FA850", "matte", rot=_aim(v), collision=False, material="leaf_grass", segments=d["fruit"], show=show)


def _truss(prefix: str, pos, heading: float, items: list, s: float, rng, d: dict, show=None, hang: bool = True,
           ripeness: dict | None = None) -> list[Part]:
    """A flower truss from the crown toward `heading`: it arches up and out and, with fruit (`hang`), bends down
    past the pot rim / trough edge. `items` are "flower", "bud" or a fruit stage, each on its own pedicel near the
    truss end. `ripeness` (Ripeness value -> stage) adds the fruit of every stage for the Ripeness variant set."""
    th = math.radians(heading)
    out = np.array([math.cos(th), math.sin(th), 0.0])
    side = np.array([-out[1], out[0], 0.0])
    x, y, z = pos
    base = np.array([x, y, z + 0.015 * s])
    if hang:
        apex, end = base + 0.06 * s * out + [0, 0, 0.06 * s], base + 0.12 * s * out - [0, 0, 0.005 * s]
    else:
        apex, end = base + 0.03 * s * out + [0, 0, 0.11 * s], base + 0.11 * s * out + [0, 0, 0.09 * s]
    path = _bez(base, apex, end, d["path"])
    parts = [_tube(f"{prefix}Stalk", path, 0.0042 * s, 0.003 * s, STALK, d["tube"], show)]
    n = len(items)
    for k, item in enumerate(items):
        start = path[-1 - min(k, len(path) - 2) // 2]  # the pedicels branch off near the end
        lat = (k - (n - 1) / 2) * 0.028 * s + rng.uniform(-0.004, 0.004)
        if item in ("flower", "bud"):
            tip = start + lat * side + 0.025 * s * out + [0, 0, 0.012 * s if hang else 0.02 * s]
            facing = out * 0.8 + [0, 0, 0.5] + side * lat * 8
        else:
            tip = start + lat * side + 0.012 * s * out - [0, 0, rng.uniform(0.022, 0.032) * s]
        mid = (start + tip) / 2 + [0, 0, 0.012 * s] + 0.006 * s * out
        parts.append(_tube(f"{prefix}Pedicel{k}", _bez(start, mid, tip, max(3, d["path"] // 2)), 0.0028 * s,
                           0.0022 * s, STALK, d["tube"], show))
        if item == "flower":
            parts += _flower(f"{prefix}F{k}", tip, facing, s, d, show)
        elif item == "bud":
            parts.append(_bud(f"{prefix}F{k}", tip, facing, s, d, show))
        elif not ripeness:
            parts += _berry(f"{prefix}B{k}", tip, item, s, rng, d, show)
        else:
            # one fruit per stage shown in the Ripeness values that use it ("Mixed" uses the item's own stage);
            # the calyx is shared. Same seed for every stage, so they hang the same way
            state = rng.random()
            by_stage: dict[str, list[str]] = {}
            for value, stage in {"Mixed": item, **ripeness}.items():
                by_stage.setdefault(stage, []).append(value)
            for j, (stage, values) in enumerate(by_stage.items()):
                g = _Rng(np.random.default_rng(int(state * 1e9)))
                parts += _berry(f"{prefix}B{k}{stage.capitalize()}", tip, stage, s, g, d,
                                {**(show or {}), "Ripeness": values}, calyx=j == 0)
                if j == 0:
                    parts[-1].show = show
    return parts


def _plant(prefix: str, x: float, y: float, z: float, rng, scale: float = 1.0) -> list[Part]:
    """A light (LITE) plant for the rack whose crown sits at (x, y, z), different every time: 5-8 leaves (some old
    and yellowing), 1-3 trusses toward the aisle (-Y) with 1-4 fruit of mixed ripeness, sometimes flowers or buds,
    and now and then a plant still only flowering. No colliders. Images as _plant_images."""
    s, d = scale, LITE
    parts = [_crown(prefix, (x, y, z), s, 10)]
    parts += _foliage(prefix, (x, y, z), rng, d, s, int(rng.choice((5, 6, 6, 7, 7, 8))), old=int(rng.choice((0, 0, 1, 2))),
                      young=rng.random() < 0.7)
    flowering = rng.random() < 0.12
    n_truss = int(rng.choice((1, 2, 2, 2, 3)))
    for t in range(n_truss):
        heading = -90 + (t - (n_truss - 1) / 2) * 34 + rng.uniform(-10, 10)
        if flowering:
            items = [rng.choice(("flower", "flower", "bud")) for _ in range(int(rng.choice((2, 3))))]
        else:
            n = int(rng.choice((1, 2, 2, 3, 3, 4)))
            ripe = ("red", "red", "turning", "white") if t == 0 else ("red", "turning", "white", "green", "green")
            items = [rng.choice(ripe) for _ in range(n)]
            if rng.random() < 0.2:
                items.append(rng.choice(("flower", "bud")))
        parts += _truss(f"{prefix}T{t}", (x, y, z), heading, items, s * rng.uniform(0.9, 1.1), rng, d,
                        hang=not flowering)
    return parts


# ---------------------------------------------------------------- growing rack

L, D = 2.40, 0.50  # rack length (X) and depth (Y)
TIERS = (0.30, 0.90, 1.50)  # top of the cross beams = bottom of each trough
TROUGH_W, TROUGH_H, TROUGH_Y = 0.28, 0.16, -0.03
PIPE_D = 0.032
H = 2.10
PLANTS_PER_TIER = 10
D_OUT = 0.528  # outer depth: the feet and pipes stick out past the post centers


def _rack(planted: bool) -> tuple[list[Part], list, list[np.ndarray]]:
    tl = L - 0.04
    xs = [-tl / 2 + (k + 0.5) * tl / PLANTS_PER_TIER for k in range(PLANTS_PER_TIER)]
    images = [*_plant_images(7101, leaf_px=3.0),
              _trough_top(tl * 1000, TROUGH_W * 1000, [(x + tl / 2) * 1000 for x in xs], 7110),
              _side(tl * 1000, TROUGH_H * 1000, 7111)]
    paint = dict(finish_="glossy", material="steel")
    parts: list[Part] = []
    px = (-L / 2 + PIPE_D / 2, 0.0, L / 2 - PIPE_D / 2)
    py = (-D / 2 + PIPE_D / 2, D / 2 - PIPE_D / 2)
    for i, x in enumerate(px):  # posts with base plates and adjuster feet
        for j, y in enumerate(py):
            parts.append(_seg(f"Post{i}{j}", (x, y, 0.012), (x, y, H), PIPE_D, PIPE, **paint))
            parts.append(_p(f"Foot{i}{j}", "cylinder", (0.06, 0.06, 0.012), (x, y, 0.006), "#9A9A9A", "metal",
                            material="steel"))
    beams = [*TIERS, H - PIPE_D / 2]
    for b, zt in enumerate(beams):  # cross beams (Y) on every post pair, rails (X) at front and back
        zc = zt - PIPE_D / 2
        for i, x in enumerate(px):
            parts.append(_seg(f"Cross{b}{i}", (x, -D / 2 + 0.002, zc), (x, D / 2 - 0.002, zc), PIPE_D * 0.85, PIPE,
                              **paint))
        for j, y in enumerate(py):
            parts.append(_p(f"Rail{b}{j}", "cylinder", (PIPE_D * 0.85, PIPE_D * 0.85, L - 0.004), (0, y, zc + 0.002),
                            PIPE, rot=(0, 90.0, 0), collision=b < 3, **paint))
    lights = []
    for t, zt in enumerate(TIERS):
        zc = zt + TROUGH_H / 2
        parts.append(_p(f"Trough{t}", "box", (tl, TROUGH_W, TROUGH_H), (0, TROUGH_Y, zc), TROUGH, "plastic",
                        faces={"top": 9, "front": 10, "back": 10}, material="plastic"))
        parts.append(_p(f"Drip{t}", "cylinder", (0.016, 0.016, tl - 0.02),
                        (0, TROUGH_Y + TROUGH_W / 2 - 0.03, zt + TROUGH_H + 0.008), TUBE, "plastic",
                        rot=(0, 90.0, 0), collision=False, material="plastic"))
        top = beams[t + 1] - PIPE_D  # under the next beams
        for k, dy in enumerate((-0.07, 0.07)):  # two LED bars per tier, lighting the plants below
            lamp, lux = _lamp(f"Led{t}{k}", (tl - 0.10, 0.05, 0.02), (0, TROUGH_Y + dy, top - 0.012), "#FBFBF6",
                              9000.0, 5000.0)
            parts.append(lamp)
            lights.append(lux)
            parts.append(_p(f"LedBody{t}{k}", "box", (tl - 0.08, 0.06, 0.012), (0, TROUGH_Y + dy, top - 0.002 + 0.004),
                            LED_BODY, "metal", collision=False, material="aluminum"))
        if planted:
            for k, x in enumerate(xs):
                rng = np.random.default_rng(7200 + 37 * t + k)
                parts += _plant(f"P{t}{k:02d}", x + rng.uniform(-0.01, 0.01), TROUGH_Y + rng.uniform(-0.01, 0.01),
                                zt + TROUGH_H, _Rng(rng), scale=rng.uniform(0.85, 1.15))
    return parts, lights, images


class _Rng:
    """random.Random-like wrapper around a numpy generator (choice of plain values)."""

    def __init__(self, g):
        self.g = g

    def random(self) -> float:
        return float(self.g.random())

    def uniform(self, a, b) -> float:
        return float(self.g.uniform(a, b))

    def choice(self, seq):
        return seq[int(self.g.integers(len(seq)))]


_RACK_DESC = (f"形は人工光型の植物工場で使う一般的なイチゴの多段栽培棚（白い塗装の鋼管の枠、長さ {L * 1000:.0f} mm・"
              f"奥行き {D * 1000:.0f} mm・高さ {H * 1000:.0f} mm、3 段、各段に幅 {TROUGH_W * 1000:.0f} mm・"
              f"高さ {TROUGH_H * 1000:.0f} mm の白い栽培槽（上面に定植穴 {PLANTS_PER_TIER} 個）と点滴チューブ、"
              "各段の上に白色 LED のバー 2 本）で、寸法・質量は代表値。正面（−Y）が通路側。")


def strawberry_growing_rack() -> Product:
    """A 3-tier strawberry growing rack with plants (leaves, flowers, white, turning and ripe fruit hanging over the
    trough edge toward the aisle). The plants are static parts of the rack without colliders."""
    parts, lights, images = _rack(True)
    return Product(slug="strawberry_growing_rack", name="イチゴの多段栽培棚（3 段・株付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, L, depth=D_OUT), mass_kg=120.0, static=True, material="steel",
                   description=_RACK_DESC + f"各段に {PLANTS_PER_TIER} 株（3 小葉の葉、花・白い実・色づいた実・赤い実を通路側へ垂らす）。"
                               "株は棚と一体の静的な部品で、当たり判定は枠と栽培槽だけ。",
                   tags=["植物工場", "イチゴ", "いちご", "栽培棚", "多段栽培", "水耕栽培", "LED", "strawberry",
                         "strawberry rack", "growing rack", "grow rack", "vertical farm", "plant factory",
                         "hydroponic rack", "strawberry plants"],
                   colors=Colors(label_base=PIPE), images=images, parts=parts, lights=lights)


def strawberry_growing_rack_empty() -> Product:
    """The same rack before planting: frame, troughs with empty planting holes, drip tubes and LEDs."""
    parts, lights, images = _rack(False)
    return Product(slug="strawberry_growing_rack_empty", name="イチゴの多段栽培棚（3 段・定植前）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, L, depth=D_OUT), mass_kg=105.0, static=True, material="steel",
                   description=_RACK_DESC + "株は無く、定植穴に培地が見える。",
                   tags=["植物工場", "イチゴ", "栽培棚", "多段栽培", "水耕栽培", "LED", "growing rack", "grow rack",
                         "vertical farm", "plant factory", "hydroponic rack", "empty rack"],
                   colors=Colors(label_base=PIPE), images=images, parts=parts, lights=lights)


# ---------------------------------------------------------------- a plant in a pot


POT_STAGES = ("Fruiting", "Flowering", "Seedling")
RIPENESS = ("Mixed", "Green", "White", "Red")


def strawberry_plant_pot() -> Product:
    """A strawberry plant in a 9 cm black nursery pot (front -Y), in detail, with two variant sets:
    Stage = Fruiting (default: fruit and a late flower over the rim) / Flowering (flowers and buds held up) /
    Seedling (a young runner plant: three small leaves and the cut runner), and Ripeness = Mixed (default) / Green /
    White / Red (the fruit of the Fruiting stage)."""
    Dp, Hp = 0.09, 0.08
    prof = [[0, 0], [0.80, 0], [0.97, 0.92], [1.0, 0.93], [1.0, 1.0], [0.94, 1.0], [0.92, 0.93], [0.76, 0.06],
            [0, 0.06]]
    z_soil = Hp - 0.008
    hs = z_soil - 0.06 * Hp
    images = [*_plant_images(7301), _soil_top(90, 7310)]
    parts = [_p("Pot", "revolve", (Dp, Dp, Hp), (0, 0, Hp / 2), POT, "plastic", profile=prof, material="plastic"),
             _p("SoilFill", "revolve", (Dp, Dp, hs), (0, 0, 0.06 * Hp + hs / 2), SOIL, "matte",
                profile=[[0, 0], [0.75, 0], [0.90, 1.0], [0, 1.0]], collision=False, material="dirt"),
             _p("Soil", "cylinder", (Dp * 0.90, Dp * 0.90, 0.002), (0, 0, z_soil + 0.001), SOIL, "matte",
                faces={"top": 9}, collision=False, material="dirt")]
    s, d, pos = 0.85, FULL, (0.0, 0.006, z_soil)
    crown = _crown("", pos, s * 0.65, 24)  # small enough for the seedling
    crown.collision = True  # the crown is the collider for the foliage
    parts.append(crown)
    grown, seedling = {"Stage": ["Fruiting", "Flowering"]}, {"Stage": ["Seedling"]}
    parts += _foliage("", pos, _Rng(np.random.default_rng(7320)), d, s, 7, show=grown)
    parts += _foliage("S", pos, _Rng(np.random.default_rng(7330)), d, s, 3, lean=60.0, show=seedling,
                      petiole=(0.05, 0.065), size=(0.032, 0.04))
    stub = np.array(pos) + [0.0, 0.0, 0.012]  # the runner cut off the mother plant
    parts.append(_tube("SRunner", _bez(stub, stub + [0.03, 0.01, 0.012], stub + [0.055, 0.016, 0.004], 6), 0.003,
                       0.0026, RUNNER, d["tube"], seedling))
    rng = _Rng(np.random.default_rng(7340))
    flowering = {"Stage": ["Flowering"]}
    parts += _truss("FT0", pos, -72, ["flower", "flower", "bud"], s, rng, d, flowering, hang=False)
    parts += _truss("FT1", pos, -112, ["flower", "bud"], s, rng, d, flowering, hang=False)
    fruiting = {"Stage": ["Fruiting"]}
    ripe = {"Green": "green", "White": "white", "Red": "red"}
    parts += _truss("T0", pos, -74, ["red", "turning", "white"], s, rng, d, fruiting, ripeness=ripe)
    parts += _truss("T1", pos, -114, ["turning", "green", "flower"], s, rng, d, fruiting, ripeness=ripe)
    return Product(slug="strawberry_plant_pot", name="イチゴの苗（9 cm ポット）", shape_class="assembly",
                   category="household", dims=Dimensions(0.175, 0.238, depth=0.227), mass_kg=0.45, material="plastic",
                   description="形は 9 cm（口径 90 mm）の黒いポリポットに植えたイチゴの株（縁がギザギザの 3 小葉の葉、"
                               "株の幅約 240 mm・高さ約 175 mm（Fruiting））で、寸法・質量は代表値。バリアント Stage で育ち具合"
                               "（Fruiting＝実と遅れて咲いた花を鉢の外へ垂らす（既定）、Flowering＝花とつぼみ、"
                               "Seedling＝ランナーから取ったばかりの小さな苗）、Ripeness で実の熟し具合"
                               "（Mixed＝赤・色づき・白・緑が混ざる（既定）、Green・White・Red）を選べる。"
                               "当たり判定は鉢と株の中心。",
                   tags=["イチゴ", "いちご", "苗", "ポット苗", "植物", "園芸", "植物工場", "strawberry plant",
                         "strawberry seedling", "potted strawberry", "plant", "seedling", "strawberry flower",
                         "strawberry fruit"],
                   colors=Colors(label_base=POT), images=images, parts=parts,
                   variant_sets={"Stage": list(POT_STAGES), "Ripeness": list(RIPENESS)})


# ---------------------------------------------------------------- floor tape


def magnetic_guide_tape() -> Product:
    """A 1 m piece of magnetic guide tape for line-following AGVs (50 mm wide), stuck to the floor."""
    c = Canvas(1000, 50, 2, "#202022", 7401)
    c.gradient(0, 0, 1000, 50, "#2A2A2C", "#18181A")
    for x in range(0, 1000, 4):  # fine rubber grain
        c.line([(x + c.rng.uniform(0, 3), 0), (x + c.rng.uniform(0, 3), 50)], "#262628", 0.3)
    img = finish(c.array(), "paper", 7401, 0.6)
    parts = [Part(name="Tape", shape="box", size=[1.0, 0.05, 0.0015], center=[0, 0, 0.00075], color="#202022",
                  finish="matte", faces={"top": 0}, material="rubber", bevel=0)]
    return Product(slug="magnetic_guide_tape", name="磁気誘導テープ（幅 50 mm・1 m）", shape_class="assembly",
                   category="environment", dims=Dimensions(0.0015, 1.0, depth=0.05), mass_kg=0.25, static=True,
                   material="rubber",
                   description="形は AGV（無人搬送車）の磁気誘導に使う一般的な床貼りの磁気テープ（幅 50 mm・厚さ 1.5 mm、"
                               "1 m に切ったもの）で、寸法・質量は代表値。並べて誘導線にする。",
                   tags=["磁気テープ", "誘導テープ", "AGV", "無人搬送車", "床", "誘導線", "植物工場", "magnetic tape",
                         "guide tape", "agv tape", "floor tape", "guide line"],
                   colors=Colors(label_base="#202022"), images=[img], parts=parts)


PRODUCTS = {f.__name__: f for f in (strawberry_growing_rack, strawberry_growing_rack_empty, strawberry_plant_pot,
                                    magnetic_guide_tape)}
