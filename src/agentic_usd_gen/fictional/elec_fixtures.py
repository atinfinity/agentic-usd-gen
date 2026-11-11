"""Fictional fixtures for an electronics store (appliance display platform, TV display stand with a digital price
display, small-appliance gondola, glass showcase counter, a pegboard with battery and bulb packs on its hooks).

The appliances that go on them come from SimReady Central. As in drug_fixtures.py, no real names or logos are used,
and shapes and sizes are the common values for each kind of fixture. Front is -Y (the customer side). Floor fixtures
are kinematic (static). Surfaces that goods go on are thin horizontal boards (so that a tool that fills shelves with goods finds them as shelves),
and nothing stands on top of a board. Signs and POP can be switched to plain with blank (Picture variant); the
digital price display is a screen (Screen variant On/Off). Packs hung on pegboard hooks are static visual parts of
the fixture, as in hc_fixtures.pegboard_wall_tools (a card resting on a thin rod is an unstable contact in PhysX).
"""

from __future__ import annotations

from ..spec import Colors, Dimensions, Part
from .base import Product
from .drug_fixtures import _header, _perforated
from .elec_goods import aa_battery_pack, led_bulb_pack
from .hc_fixtures import _holes, _hook_grid, _pegboard_parts
from .hc_tools import place
from .paint import Canvas, finish, mix, trim_safe
from .products import INK, _box, _face, _price_strip
from .super_fixtures import _pop, _sign

ELEC_PLACES = ["electronics_store"]
WHITE, STEEL, GRAY, DARK = "#F4F5F7", "#C4C8CC", "#5A5F66", "#2A2D33"
GLASS = "#EAF2F5"
RED, BLUE, YELLOW = "#D32F2F", "#1565C0", "#FFD600"


def _bolt(c: Canvas, cx: float, cy: float, r: float) -> None:
    """A lightning bolt (electricity)."""
    c.polygon([(cx + r * 0.15, cy - r), (cx - r * 0.55, cy + r * 0.1), (cx - r * 0.05, cy + r * 0.1),
               (cx - r * 0.2, cy + r), (cx + r * 0.55, cy - r * 0.15), (cx + r * 0.05, cy - r * 0.15)],
              fill="#FFFFFF")


def _pop_price(w_mm: float, h_mm: float, title: str, price: str, seed: int) -> Canvas:
    """A yellow price POP with a red price (the usual electronics store style)."""
    c = Canvas(w_mm, h_mm, None, YELLOW, seed)
    c.gradient(0, 0, w_mm, h_mm, "#FFF176", YELLOW)
    c.rect(0, 0, w_mm, h_mm * 0.22, fill=RED)
    c.text(w_mm / 2, h_mm * 0.11, "当店おすすめ", h_mm * 0.13, "#FFFFFF", 900)
    c.text(w_mm / 2, h_mm * 0.36, title, h_mm * 0.12, INK, 900, max_w=w_mm * 0.9)
    c.text(w_mm / 2, h_mm * 0.62, price, h_mm * 0.26, RED, 900, max_w=w_mm * 0.92)
    c.text(w_mm / 2, h_mm * 0.84, "税込・ポイント 10% 還元（架空）", h_mm * 0.07, INK, 800, max_w=w_mm * 0.9)
    c.rect(0, h_mm * 0.94, w_mm, h_mm, fill=RED)
    return c


# ---------------------------------------------------------------- low display platform for large appliances


def appliance_display_platform() -> Product:
    W, D = 1.80, 0.90
    top_z, t = 0.12, 0.018
    pop_h = 0.40
    H = 1.40
    head = _header(1800, 160, "生活家電", "HOME APPLIANCES  冷蔵庫・洗濯機", 9991, BLUE, band=YELLOW, icon=_bolt)
    pops = [_face(_pop_price(300, 400, t_, p, 9992 + k).array(), "paper", 9992 + k, 0.4, 6)
            for k, (t_, p) in enumerate((("省エネ 冷蔵庫", "128,000円"), ("ドラム式 洗濯機", "198,000円")))]
    skirt = Canvas(1800, 100, None, "#E9EBEE", 9995)
    skirt.gradient(0, 0, 1800, 100, "#F4F5F7", "#D9DCE0")
    skirt.rect(0, 0, 1800, 12, fill=BLUE)
    for k in range(6):
        skirt.text(150 + k * 300, 58, "展示品 / DISPLAY", 26, GRAY, 800)
    skirt_img = _face(skirt.array(), "plastic", 9995, 0.3, 4)
    parts = [
        _box("Base", (W - 0.02, D - 0.02, top_z - t), (0, 0, (top_z - t) / 2), "#E9EBEE", "plastic", {"front": 3}),
        _box("Top", (W, D, t), (0, 0, top_z - t / 2), "#D9DCE0", "plastic"),
        # the header stands behind the platform on two posts fixed to its back edge
        _box("PostLeft", (0.04, 0.04, H - top_z + 0.10), (-W / 2 + 0.06, D / 2 + 0.02, top_z - 0.10 +
                                                           (H - top_z + 0.10) / 2), STEEL, "metal"),
        _box("PostRight", (0.04, 0.04, H - top_z + 0.10), (W / 2 - 0.06, D / 2 + 0.02, top_z - 0.10 +
                                                            (H - top_z + 0.10) / 2), STEEL, "metal"),
        _sign("Header", (W, 0.02, 0.16), (0, D / 2 + 0.02, H - 0.08), BLUE, {"front": 0}, mix(BLUE, "#FFFFFF", 0.1),
              collision=True, material="plastic"),
    ]
    for k, x in enumerate((-0.45, 0.45)):  # price POPs on the header posts' crossbar height
        parts.append(_sign(f"Pop{k}", (0.30, 0.006, pop_h), (x, D / 2 + 0.013, H - 0.20 - pop_h / 2), YELLOW,
                           {"front": 1 + k}, "#FFF8D0", collision=False))
    parts.append(_box("PopBar", (W - 0.12, 0.012, 0.02), (0, D / 2 + 0.02, H - 0.19), STEEL, "metal",
                      collision=False))
    return Product(slug="appliance_display_platform", name="大型家電の展示台 1800mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.04), mass_kg=40.0, static=True,
                   material="steel",
                   description="形は家電量販店で冷蔵庫・洗濯機などの大型家電を並べる一般的な低い展示台（幅 1800 mm・奥行き "
                               "900 mm・高さ 120 mm、後ろの支柱に売場の表示と価格の POP 2 枚）で、寸法・質量は代表値。"
                               "家電は載せていない（SimReady などのアセットを台に置く）。表示・価格の文字は架空。",
                   tags=["展示台", "家電", "大型家電", "冷蔵庫", "洗濯機", "ステージ", "店舗什器", "家電量販店",
                         "appliance display", "display platform", "electronics store"], photos=[],
                   colors=Colors(label_base="#E9EBEE"), images=[head, *pops, skirt_img], parts=parts,
                   picture_places=ELEC_PLACES)


# ---------------------------------------------------------------- TV display stand with a digital price display


def tv_display_stand() -> Product:
    W, D, H = 1.80, 0.60, 2.00
    low_z, t = 0.45, 0.018  # the counter for large TVs
    up_z, up_d = 1.15, 0.32  # the upper shelf for small TVs
    back_t = 0.03
    y_back = D / 2 - back_t
    head = _header(1800, 200, "テレビ・レコーダー", "TV & RECORDERS  4K・有機EL", 10001, DARK, band=RED, icon=_bolt)
    # the digital price display (finish "screen", Screen variant)
    s = Canvas(560, 160, None, "#0A0D14", 10002)
    s.gradient(0, 0, 560, 160, "#14213D", "#060A14")
    s.rect(0, 0, 560, 34, fill=RED)
    s.text(280, 17, "本日のおすすめ  TODAY'S DEAL", 20, "#FFFFFF", 900)
    s.text(150, 92, "4K テレビ 55V", 28, "#FFFFFF", 800)
    s.text(420, 92, "99,800円", 44, YELLOW, 900)
    s.text(280, 140, "長期保証 5 年無料（架空）", 18, "#9FB3D9", 700)
    screen = trim_safe(finish(s.array(), "screen", 10002, 0.6))
    back = _perforated(1740, 1300, 10003, "#3A3D44")
    parts = [
        _box("Counter", (W, D - back_t, low_z - t), (0, -back_t / 2, (low_z - t) / 2), DARK, "matte"),
        _box("CounterTop", (W, D - back_t, t), (0, -back_t / 2, low_z - t / 2), "#1E2024", "plastic"),
        _box("BackPanel", (W - 0.06, back_t, H - 0.25 - low_z), (0, y_back + back_t / 2, low_z + (H - 0.25 - low_z) / 2),
             "#3A3D44", "metal", {"front": 2}),
        _box("SideLeft", (0.03, D, H - 0.20), (-W / 2 + 0.015, 0, (H - 0.20) / 2), DARK, "metal"),
        _box("SideRight", (0.03, D, H - 0.20), (W / 2 - 0.015, 0, (H - 0.20) / 2), DARK, "metal"),
        _box("UpperShelf", (W - 0.06, up_d, t), (0, y_back - up_d / 2, up_z), "#1E2024", "metal"),
        _sign("Header", (W, 0.03, 0.20), (0, y_back + back_t / 2, H - 0.10), DARK, {"front": 0},
              mix(DARK, "#FFFFFF", 0.1), collision=True, material="plastic"),
        # the frame sits on the back panel, the screen in front of it
        _box("PriceDisplayFrame", (0.58, 0.004, 0.18), (0, y_back - 0.002, H - 0.33), "#15171B", "plastic",
             collision=False),
        _box("PriceDisplay", (0.56, 0.008, 0.16), (0, y_back - 0.008, H - 0.33), "#0A0D14", "screen", {"front": 1},
             collision=False),
    ]
    return Product(slug="tv_display_stand", name="テレビの展示台（デジタル価格表示付き）1800mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=95.0, static=True, material="steel",
                   description="形は家電量販店でテレビを並べる一般的な展示台（幅 1800 mm・奥行き 600 mm・高さ 2000 mm、"
                               "高さ 450 mm の台と上の浅い棚・背板・売場の表示・デジタルの価格表示）で、寸法・質量は代表値。"
                               "テレビは載せていない（SimReady などのアセットを置く）。価格表示は Screen バリアントで消せる。"
                               "表示・価格の文字は架空。",
                   tags=["テレビ台", "展示台", "テレビ", "デジタルサイネージ", "価格表示", "店舗什器", "家電量販店",
                         "tv display stand", "tv shelf", "digital price display", "electronics store"], photos=[],
                   colors=Colors(label_base=DARK), images=[head, screen, back], parts=parts,
                   picture_places=ELEC_PLACES)


# ---------------------------------------------------------------- small-appliance gondola


def small_appliance_gondola() -> Product:
    W, D, H = 0.90, 0.60, 1.80
    back_h = 1.60
    sd = 0.50
    y_back = D / 2 - 0.03
    ys = y_back - sd / 2
    imgs = [_perforated(900, 1500, 10011),
            _price_strip(["3,980円", "12,800円", "5,480円", "8,980円", "19,800円", "2,980円"], 870, 10012, 142),
            _header(900, 200, "調理家電", "KITCHEN APPLIANCES  炊飯器・電子レンジ", 10013, RED, band=YELLOW, icon=_bolt)]
    parts = [
        _box("BasePlinth", (W, D - 0.02, 0.10), (0, -0.01, 0.05), GRAY, "matte"),
        _box("BaseShelf", (W - 0.04, D - 0.06, 0.015), (0, -0.02, 0.1075), STEEL, "metal"),
        _box("BackPanel", (W, 0.03, back_h - 0.10), (0, D / 2 - 0.015, 0.10 + (back_h - 0.10) / 2), "#E6E8EB",
             "plastic", {"front": 0}),
        _box("SideLeft", (0.02, D, back_h), (-W / 2 + 0.01, 0, back_h / 2), GRAY, "metal"),
        _box("SideRight", (0.02, D, back_h), (W / 2 - 0.01, 0, back_h / 2), GRAY, "metal"),
        _sign("Header", (W, 0.02, H - back_h), (0, D / 2 - 0.02, back_h + (H - back_h) / 2), RED, {"front": 2},
              "#E6E8EB", collision=True, material="plastic"),
        _box("BaseRail", (W - 0.04, 0.012, 0.035), (0, -D / 2 + 0.016, 0.10), "#FFFFFF", "plastic", {"front": 1},
             collision=False),
    ]
    for k, z in enumerate((0.55, 1.00)):  # tall pitches for boxed appliances
        parts += [_box(f"Shelf{k + 1}", (W - 0.04, sd, 0.015), (0, ys, z), STEEL, "metal"),
                  _box(f"PriceRail{k + 1}", (W - 0.04, 0.012, 0.035), (0, ys - sd / 2 - 0.006, z - 0.008), "#FFFFFF",
                       "plastic", {"front": 1}, collision=False)]
    parts.append(_box("Shelf3", (W - 0.04, 0.36, 0.015), (0, y_back - 0.18, 1.38), STEEL, "metal"))
    return Product(slug="small_appliance_gondola", name="小型家電のゴンドラ 900mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=60.0, static=True, material="steel",
                   description="形は家電量販店の小型家電の売場の一般的なゴンドラ（幅 900 mm・奥行き 600 mm・高さ 1800 mm、"
                               "有孔の背板・深い棚板 2 段と浅い最上段・台の棚・値札レール・案内表示）で、寸法・質量は代表値。"
                               "炊飯器・電子レンジなどの箱を並べる深い棚。案内表示の文字は架空。",
                   tags=["ゴンドラ", "陳列棚", "小型家電", "調理家電", "店舗什器", "家電量販店", "gondola",
                         "appliance shelf", "electronics store"], photos=[],
                   colors=Colors(label_base="#E6E8EB"), images=imgs, parts=parts, picture_places=ELEC_PLACES)


# ---------------------------------------------------------------- glass showcase counter


def glass_showcase() -> Product:
    W, D, H = 1.20, 0.50, 0.95
    base_h = 0.20
    t = 0.008  # glass
    kick = Canvas(1200, 200, None, "#1E2024", 10021)
    kick.gradient(0, 0, 1200, 200, "#2A2D33", "#15171B")
    kick.rect(0, 0, 1200, 10, fill=BLUE)
    kick.text(600, 80, "スマートフォン・カメラ", 64, "#FFFFFF", 900)
    kick.text(600, 150, "SMARTPHONES & CAMERAS  お気軽にお声がけください", 26, "#9FB3D9", 800, spacing=2)
    kick_img = _face(kick.array(), "plastic", 10021, 0.3, 4)
    parts = [
        _box("Base", (W, D, base_h), (0, 0, base_h / 2), "#1E2024", "plastic", {"front": 0},
             blank="#1E2024"),
        _box("Floor", (W - 0.04, D - 0.04, 0.012), (0, 0, base_h + 0.006), WHITE, "plastic"),
        _box("GlassShelf", (W - 0.04, D - 0.12, t), (0, 0.02, base_h + 0.36), GLASS, "glass", thin_walled=True),
        _box("GlassTop", (W, D, t), (0, 0, H - t / 2), GLASS, "glass", thin_walled=True),
        _box("GlassFront", (W, t, H - base_h - t), (0, -D / 2 + t / 2, base_h + (H - base_h - t) / 2), GLASS, "glass",
             thin_walled=True),
        _box("GlassLeft", (t, D - 2 * t, H - base_h - t), (-W / 2 + t / 2, 0, base_h + (H - base_h - t) / 2), GLASS,
             "glass", thin_walled=True),
        _box("GlassRight", (t, D - 2 * t, H - base_h - t), (W / 2 - t / 2, 0, base_h + (H - base_h - t) / 2), GLASS,
             "glass", thin_walled=True),
        # staff side (+Y): two sliding glass doors, shown closed (no joints)
        _box("DoorLeft", (W / 2 + 0.02, t, H - base_h - t - 0.01), (-W / 4 + 0.01, D / 2 - t / 2,
                                                                     base_h + (H - base_h - t) / 2), GLASS, "glass",
             thin_walled=True),
        _box("DoorRight", (W / 2 + 0.02, t, H - base_h - t - 0.01), (W / 4 - 0.01, D / 2 - 1.5 * t - 0.002,
                                                                      base_h + (H - base_h - t) / 2), GLASS, "glass",
             thin_walled=True),
    ]
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):  # aluminum corner posts
        parts.append(_box(f"Corner{k}", (0.012, 0.012, H - base_h), (sx * (W / 2 - 0.006), sy * (D / 2 - 0.006),
                                                                       base_h + (H - base_h) / 2), "#B9BEC4", "metal",
                          collision=False))
    return Product(slug="glass_showcase", name="ガラスショーケース 1200mm", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=75.0, static=True, material="glass",
                   description="形は家電量販店・カメラ売場の一般的なカウンター型のガラスショーケース（幅 1200 mm・奥行き "
                               "500 mm・高さ 950 mm、ガラスの天板・前面・側面と中のガラス棚・店員側の引き違い戸・台の表示）で、"
                               "寸法・質量は代表値。引き戸は閉じた状態で固定（関節なし）。台の表示の文字は架空。",
                   tags=["ショーケース", "ガラスケース", "カウンター", "スマホ", "カメラ", "店舗什器", "家電量販店",
                         "glass showcase", "display case", "showcase counter", "electronics store"], photos=[],
                   colors=Colors(label_base="#1E2024"), images=[kick_img], parts=parts, picture_places=ELEC_PLACES)


def pegboard_batteries_bulbs() -> Product:
    """The pegboard gondola of hc_fixtures with AA battery and LED bulb packs hanging on its hooks (static, visual)."""
    W, D, H = 0.90, 0.60, 1.80
    rows = (1.00, 1.25, 1.50)
    hooks = _hook_grid(W, rows, 3)
    imgs = [_holes(860, 1480, 4471), _pop(860, 180, "電池・電球", "単3 アルカリ 4本  LED電球 E26", 4472, BLUE, WHITE,
                                          YELLOW)]
    parts, yb = _pegboard_parts(W, D, H, 0, 1, hooks)
    packs = {}
    for name, f in (("aa", aa_battery_pack), ("led", led_bulb_pack)):
        p = f()
        packs[name] = (p, len(imgs))
        imgs += p.images
    plan = {1.50: ("aa", "aa", "aa"), 1.25: ("aa", "aa", "led"), 1.00: ("led", "led", "led")}
    for n, (x, z) in enumerate(hooks):
        key = plan[z][n % 3]
        pack, k = packs[key]
        step = pack.size[1] + 0.008
        dys = [0.03 + pack.size[1] / 2 + m * step for m in range(4) if 0.03 + pack.size[1] + m * step <= 0.245]
        for m, dy in enumerate(dys):  # packs on each hook, front to back, the hang hole on the hook
            parts += place(pack, f"{key}{n}_{m}_", x, yb - dy, z + 0.012 - pack.size[2], k, collision=False)
    return Product(slug="pegboard_batteries_bulbs", name="有孔ボードの電池・電球売場 900mm（フックに商品付き）",
                   shape_class="assembly", category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=50.0,
                   static=True, material="steel",
                   description="形は hc_fixtures の pegboard_gondola と同じ有孔ボードのゴンドラに、単3形アルカリ乾電池 4 本パックと "
                               "LED 電球（aa_battery_blister・led_bulb_blister と同じ絵）をフックに吊ったもので、寸法・質量は代表値。"
                               "吊った商品は什器の一部（見た目だけ・当たり判定なし・動かない）。下の台と低い棚は 商品を並べられる。"
                               "POP の文字は架空。",
                   tags=["有孔ボード", "ペグボード", "フック", "電池", "乾電池", "電球", "LED電球", "店舗什器", "家電量販店",
                         "ホームセンター", "pegboard", "battery display", "light bulb display", "hook display",
                         "electronics store"],
                   photos=[], colors=Colors(label_base=DARK), images=imgs, parts=parts,
                   picture_places=[*ELEC_PLACES, "home_center", "shop"])


PRODUCTS = {f.__name__: f for f in (appliance_display_platform, tv_display_stand, small_appliance_gondola,
                                    glass_showcase, pegboard_batteries_bulbs)}
