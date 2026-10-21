"""人型キャラクター(2.5 頭身)の生成。骨組みのポーズ × 見た目の設定(髪・帽子・服・持ち物)で 12 フレームを描く。

座標は右向き。脚・腕の角度は「真下 = 0°、前(右) = +」。肘・膝の角度は 1 つ上の骨からの相対角。
"""
import math
from pwlib import tint
from engine import Canvas, Palette, T, ellipse, rect, rrect, capsule, poly, union, minus, inter

THIGH, SHIN = 4.6, 4.4
UPPER, FORE = 3.6, 3.4
TORSO = 9.0
HEAD_R = (6.6, 6.1)
BODY_SX = 0.62  # 胴まわり(服・スカート・マントを含む)の横幅の倍率。頭には影響しない

# ---- ポーズ ----
# hip: 腰の位置(None なら足が地面に着くよう自動)/ lean: 体の傾き(+ = 前)/ nl,fl: 手前・奥の脚 /
# na,fa: 手前・奥の腕 / hand: 手の目標位置(腕を曲げて届かせる)/ head: 頭の傾き / eyes: 目の状態
TOP = 10  # 背の高い帽子のための、上の余白(最後に空の行は切り詰める)
GROUND = 34.4 + TOP  # 足の裏の高さ(この下の行が輪郭)

POSES = {
    'idle': dict(x=17.5, lean=0, nl=(4, 0), fl=(-4, 0), na=(10, 8), fa=(-8, 8)),
    # 歩き: walk1(手前の脚で踏み出す)→ walk3(手前の脚で立ち、奥の脚の膝を上げて前へ)→ walk2(奥の脚で踏み出す)
    # → walk4(奥の脚で立ち、手前の脚を前へ)の 4 枚。脚を交差させる 2 枚では腰が上がるので、体も上下する
    'walk1': dict(x=17.5, lean=4, nl=(26, -6), fl=(-24, -16), na=(-26, 18), fa=(28, 28)),
    'walk2': dict(x=17.5, lean=4, nl=(-24, -16), fl=(26, -6), na=(28, 28), fa=(-26, 18)),
    'walk3': dict(x=17.5, lean=3, nl=(2, -2), fl=(24, -70), na=(-6, 14), fa=(6, 18)),
    'walk4': dict(x=17.5, lean=3, nl=(24, -70), fl=(2, -2), na=(6, 18), fa=(-6, 14)),
    'jump': dict(x=17.5, y=25.0, lean=6, nl=(62, -88), fl=(-12, -38), na=(75, 35), fa=(-40, 20)),
    'fall': dict(x=17.5, y=23.5, lean=-4, nl=(18, -30), fl=(-14, -12), na=(95, 35), fa=(-110, -20)),
    'sit': dict(x=15.5, y=29.6, lean=-6, nl=(90, -88), fl=(84, -84), na=(55, 25), fa=(48, 30), sit=True),
    'sleep': dict(x=12.5, y=29.5, lean=90, nl=(-90, 0), fl=(-84, -4), na=(-12, 0), fa=(-30, 0), eyes='closed',
                  head=0),
}

# よじ登り(44x48、ax=28)。L = 足場の角の行。手は (35, L) の近く
HANG_W, HANG_H, HANG_AX = 44, 48, 28
HANG = {
    'hang1': dict(L=19, x=27.2, y=19 + 15.5, lean=0, nl=(4, -4), fl=(-8, -8), hand=True),
    'hang2': dict(L=19, x=27.2, y=19 + 15.5, lean=-3, nl=(-14, -6), fl=(12, -10), hand=True),
    'pull1': dict(L=25, x=27.6, y=25 + 9.5, lean=8, nl=(30, -60), fl=(-6, -10), hand=True),
    'pull2': dict(L=31, x=27.8, y=31 + 3.5, lean=26, nl=(80, -110), fl=(-10, -16), hand=True),
    'pull3': dict(L=37, x=28.6, y=37 - 2.0, lean=30, nl=(100, -120), fl=(20, -40), hand=True, knee=True),
}


def limb(x, y, a1, a2, l1, l2):
    """角度で曲げた 2 本の骨の、関節と先端の位置"""
    r1 = math.radians(a1)
    jx, jy = x + l1 * math.sin(r1), y + l1 * math.cos(r1)
    r2 = math.radians(a1 + a2)
    return (jx, jy), (jx + l2 * math.sin(r2), jy + l2 * math.cos(r2))


def ik(sx, sy, tx, ty, l1, l2, bend=1):
    """肩 (sx,sy) から目標 (tx,ty) に手を届かせる肘の位置。届かなければ伸ばしきる"""
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    d2 = min(d, l1 + l2 - 0.01)
    if d < 1e-6:
        return (sx, sy + l1), (sx, sy + l1 + l2)
    ux, uy = dx / d, dy / d
    a = (l1 * l1 - l2 * l2 + d2 * d2) / (2 * d2)
    h = math.sqrt(max(0, l1 * l1 - a * a))
    jx, jy = sx + ux * a - uy * h * bend, sy + uy * a + ux * h * bend
    ex, ey = sx + ux * d2, sy + uy * d2
    return (jx, jy), (ex, ey)


class Look:
    """見た目の設定(辞書)に既定値を補う"""
    DEF = dict(skin='#f2c9a5', hair='#5a3a26', hair_style='short', hat=None, hat_col='#c0392b', hat_col2='#f4f1ea',
               shirt='#4a7bd0', sleeve='short', pants='#3d4a66', shoes='#5a3f2c', eyes='normal', eye_col=None,
               outline=None, skirt=None, robe=None, cape=None, belt=None, apron=None, tie=None, coat=None,
               item=None, item_col='#c9ccd4', wings=None, tail=None, ears=None, blush=True, mouth=True,
               beard=None, glasses=None, head_shape='round', gloves=None, collar=None, buttons=None,
               boots=None, scarf=None, pattern=None, extra=None, legs_hidden=False, skin_ramp=None)

    def __init__(self, d):
        self.__dict__.update(self.DEF)
        self.__dict__.update(d)


def draw(look, pose, w=36, h=36, hang=None, pal=None):
    pal = pal or Palette(look.outline or '#2b2233')
    R = lambda c: pal.ramp(c)
    far = lambda c: pal.ramp(c, light=1.05, shadow=0.72, dark=0.55)
    cv = Canvas(w, h, pal)
    # 肌は影を浅く(濃いオレンジの影が顔を汚して見せないように)
    skin = pal.ramp(look.skin, light=1.12, shadow=0.9, dark=0.8)
    skin_f = pal.ramp(look.skin, light=1.0, shadow=0.84, dark=0.72)
    shirt, shirt_f = R(look.shirt), far(look.shirt)
    pants, pants_f = R(look.pants), far(look.pants)
    shoes, shoes_f = R(look.shoes), far(look.shoes)
    hairR = R(look.hair)

    p = dict(pose)
    # ---- 骨組み ----
    x = p['x']
    lean = p.get('lean', 0)
    nl, fl = p['nl'], p['fl']
    if 'y' in p:
        y = p['y'] + TOP
    else:  # 低い方の足が地面に着く高さ
        fy = max(limb(0, 0, a1, a2, THIGH, SHIN)[1][1] for a1, a2 in (nl, fl))
        y = GROUND - 1.0 - fy
    hip = T(x, y, lean, sx=BODY_SX)
    neck = hip.apply(0, -TORSO)
    sh = hip.apply(0.3, -TORSO + 1.6)  # 肩
    hipN = hip.apply(0.6, -0.6)
    hipF = hip.apply(-0.9, -0.6)

    def leg(base, a, ramp, sramp, pid_far):
        (kx, ky), (fx, fy) = limb(base[0], base[1], a[0] + lean * 0, a[1], THIGH, SHIN)
        legs = union(capsule(base[0], base[1], kx, ky, 2.15), capsule(kx, ky, fx, fy, 2.0, 1.9))
        ang = a[0] + a[1]
        ft = T(fx, fy, -ang if abs(ang) < 60 else 0)
        foot = ellipse(1.1, 0.25, 2.5, 1.45)
        return legs, ft, foot, (kx, ky), (fx, fy)

    def arm(near, a=None, target=None):
        ramp = shirt if near else shirt_f
        sramp = skin if near else skin_f
        sx, sy = sh[0] + (0.4 if near else -0.8), sh[1]
        if target:
            (ex, ey), (hx, hy) = ik(sx, sy, target[0], target[1], UPPER, FORE, bend=-1)
        else:
            (ex, ey), (hx, hy) = limb(sx, sy, a[0], a[1], UPPER, FORE)
        return (sx, sy), (ex, ey), (hx, hy), ramp, sramp

    ident = T()
    # 手の位置
    if hang:
        L = hang['L'] + TOP
        tgtN, tgtF = (36.6, L - 0.4), (35.2, L - 0.2)
        armN = arm(True, target=tgtN)
        armF = arm(False, target=tgtF)
    else:
        armN = arm(True, p['na'])
        armF = arm(False, p['fa'])

    def draw_arm(a, near):
        (sx, sy), (ex, ey), (hx, hy), ramp, sramp = a
        sl = look.sleeve
        if look.robe and look.robe.get('sleeve'):
            r1 = 2.3
        else:
            r1 = 1.75
        if sl == 'long' or sl == 'robe':
            cv.shape(union(capsule(sx, sy, ex, ey, r1), capsule(ex, ey, hx, hy, r1 - 0.1, 1.6)), ident, ramp)
        elif sl == 'none':
            cv.shape(union(capsule(sx, sy, ex, ey, 1.6), capsule(ex, ey, hx, hy, 1.5)), ident, sramp)
        else:  # 半袖
            mx, my = sx + (ex - sx) * 0.75, sy + (ey - sy) * 0.75
            cv.shape(union(capsule(mx, my, ex, ey, 1.55), capsule(ex, ey, hx, hy, 1.5)), ident, sramp)
            cv.shape(capsule(sx, sy, mx, my, 1.95), ident, ramp)
        gl = look.gloves
        hr = gl and R(gl) if near else gl and far(gl)
        cv.shape(ellipse(hx, hy, 1.75, 1.75), ident, hr or sramp)
        return (hx, hy)

    def draw_leg(base, a, near):
        ramp = pants if near else pants_f
        sramp = shoes if near else shoes_f
        legs, ft, foot, knee, fpt = leg(base, a, ramp, sramp, not near)
        if look.legs_hidden:
            cv.shape(foot, ft, sramp)
            return knee, fpt
        bl = look.boots
        cv.shape(legs, ident, ramp)
        if bl:
            br = R(bl) if near else far(bl)
            (kx, ky), (fx, fy) = knee, fpt
            cv.shape(capsule(kx + (fx - kx) * 0.35, ky + (fy - ky) * 0.35, fx, fy, 2.15), ident, br)
            cv.shape(foot, ft, br)
        else:
            cv.shape(foot, ft, sramp)
        return knee, fpt

    # ---- 奥から順に塗る ----
    # 翼(背中)
    if look.wings:
        wcol = R(look.wings['col'])
        flap = {'idle': 0, 'walk1': 10, 'walk2': -10, 'jump': -25, 'fall': 25}.get(pose.get('name'), 0)
        wt = hip.then(-3.0, -TORSO + 2.5, -30 + flap)
        kind = look.wings.get('kind', 'feather')
        if kind == 'bat':
            shp = poly([(0, 0), (-4, -7), (-10, -5), (-12, 1), (-9, 0), (-7, 3), (-4, 1), (-2, 4)])
        elif kind == 'fairy':
            shp = union(ellipse(-5, -4, 5.5, 3.3), ellipse(-4, 2, 3.6, 2.4))
        else:
            shp = union(ellipse(-5, -2.5, 6.2, 3.6), ellipse(-9, 1, 3.5, 2.2), ellipse(-6.5, 2.5, 3.6, 2.0))
        cv.shape(shp, wt, wcol)
    # しっぽ
    if look.tail:
        tc = R(look.tail['col'])
        tt = hip.then(-3.5, -1.5, 0)
        kind = look.tail.get('kind', 'devil')
        if kind == 'devil':
            cv.shape(union(capsule(0, 0, -4, 1.5, 0.9), capsule(-4, 1.5, -6, -2.5, 0.9),
                           poly([(-7.8, -2.6), (-5.4, -5.4), (-4.2, -2.4)])), tt, tc)
        elif kind == 'fluffy':
            cv.shape(union(capsule(0, 0, -4, -2, 1.7, 2.6), ellipse(-5, -3.5, 2.6, 3.0)), tt, tc)
        elif kind == 'cat':
            cv.shape(union(capsule(0, 0, -4, -1, 1.0), capsule(-4, -1, -5, -6, 1.0)), tt, tc)
    # マント(背中)
    if look.cape:
        cc = far(look.cape)
        swing = {'walk1': -8, 'walk2': -4, 'walk3': -6, 'walk4': -6, 'jump': 18, 'fall': -22}.get(pose.get('name'), 0)
        ct = hip.then(-0.5, -TORSO + 1.2, swing)
        cv.shape(poly([(-3.5, 0), (3.0, 0), (1.0, 9.5), (-8.5, 11.5)]), ct, cc)
    # 長い髪(背中側)
    # 頭は胴の横幅の倍率(BODY_SX)を引き継がない
    head_t = T(*hip.apply(0.6, -TORSO - 5.6), lean + p.get('head', 0))
    if lean == 90:
        head_t = T(neck[0] + 5.6, neck[1] - 0.6, -90)
    hs = look.hair_style
    if hs in ('long', 'twin', 'pony', 'braid'):
        if hs == 'long':
            cv.shape(rrect(-6.6, -2.0, -0.5, 9.0, 2.6), head_t, hairR)
        elif hs == 'twin':
            cv.shape(union(capsule(-5.5, -1, -6.5, 7.5, 2.3, 1.6)), head_t, hairR)
        elif hs == 'pony':
            cv.shape(capsule(-5.5, -2.5, -9.0, 5.0, 2.4, 1.4), head_t, hairR)
        elif hs == 'braid':
            cv.shape(union(capsule(-5.0, 0, -5.5, 8.0, 1.6), ellipse(-5.5, 9, 1.6, 1.2)), head_t, hairR)
    # 奥の腕・奥の脚
    hand_f = draw_arm(armF, False)
    draw_leg(hipF, fl, False)
    # 胴
    tor = rrect(-4.3, -TORSO - 0.4, 4.3, 0.9, 2.6)
    cv.shape(tor, hip, shirt)
    if look.coat:  # 前を開けた上着(白衣など)
        cv.shape(union(rrect(-4.5, -TORSO - 0.4, 0.8, 4.2, 1.6), rrect(2.6, -TORSO - 0.4, 4.6, 4.2, 1.0)),
                 hip, R(look.coat), line=True)
    if look.apron:
        cv.shape(rrect(0.6, -TORSO + 2.5, 4.7, 4.5, 1.0), hip, R(look.apron))
    if look.collar:
        cv.shape(poly([(-2, -TORSO - 0.4), (3.6, -TORSO - 0.4), (1.6, -TORSO + 3.0)]), hip, R(look.collar))
    if look.tie:
        cv.shape(poly([(2.6, -TORSO + 0.4), (3.8, -TORSO + 0.4), (3.9, -TORSO + 5.5), (3.2, -TORSO + 6.4),
                       (2.5, -TORSO + 5.5)]), hip, R(look.tie), line=False)
    if look.scarf:
        cv.shape(union(rrect(-4.4, -TORSO - 0.8, 4.4, -TORSO + 1.4, 1.0), capsule(-3, -TORSO + 0.6, -5.5, -TORSO + 4, 1.0)),
                 hip, R(look.scarf))
    if look.buttons:
        for by in (-6.5, -4.0, -1.5):
            cv.dot(hip, 3.0, by, pal.sym(look.buttons))
    if look.belt:
        cv.shape(rect(-4.4, -1.8, 4.4, -0.4), hip, R(look.belt), line=False)
        cv.dot(hip, 3.0, -1.1, pal.sym('#e8c860'))
    # スカート・ローブ(脚の上)
    knee_n = None
    if not (look.robe or look.skirt):
        knee_n, _ = draw_leg(hipN, nl, True)
    if look.skirt:
        if not p.get('sit') and lean != 90:
            draw_leg(hipN, nl, True)
        sk = look.skirt
        cv.shape(poly([(-4.6, -1.8), (4.6, -1.8), (6.4, 4.8), (-6.2, 4.8)]), hip, R(sk))
        if p.get('sit') or lean == 90:
            draw_leg(hipN, nl, True)
    if look.robe:
        rc = R(look.robe['col'])
        if p.get('sit') or lean == 90 or hang:
            draw_leg(hipN, nl, True)
            cv.shape(poly([(-4.6, -3), (4.6, -3), (5.8, 5.5), (-5.6, 5.5)]), hip, rc)
        else:
            sw = {'walk1': 1.5, 'walk2': -1.0}.get(pose.get('name'), 0)
            ln = 9.6 if pose.get('name') not in ('jump', 'fall') else 7.5
            cv.shape(poly([(-4.6, -3), (4.6, -3), (6.2 + sw, ln), (-6.0 + sw, ln)]), hip, rc)
            draw_leg(hipN, nl, True) if False else None
        if look.robe.get('trim'):
            pass
    # 頭と手前の腕(ぶら下がりでは腕が顔にかからないよう、腕を先に)
    if hang:
        draw_arm(armN, True)
    draw_head(cv, pal, look, head_t, p.get('eyes', 'open'))
    if not hang:
        draw_arm(armN, True)
    if look.item and not hang:
        draw_item(cv, pal, look, armN, pose)
    return cv


def draw_head(cv, pal, look, t, eyes):
    R = lambda c: pal.ramp(c)
    skin = pal.ramp(look.skin, light=1.12, shadow=0.9, dark=0.8)
    hairR = R(look.hair)
    hs = look.hair_style
    rx, ry = HEAD_R
    # 頭(肌)
    if look.head_shape == 'box':
        head = rrect(-rx, -ry, rx, ry + 0.3, 2.2)
    else:
        head = ellipse(0, 0, rx, ry)
    hid = cv.shape(head, t, skin, line=False)
    # 耳(けもの耳・とがった耳は帽子の前)
    if look.ears == 'elf':
        cv.shape(poly([(-2.5, -0.5), (-7.5, -4.5), (-2.0, 2.0)]), t, skin)
    elif look.ears not in ('cat', 'bunny', 'none', None) or look.ears is None:
        if hs != 'long' and look.hat not in ('helmet', 'astro', 'ninja', 'hood', 'knight'):
            cv.shape(ellipse(-1.6, 1.0, 1.3, 1.7), t, skin, line=False)
    # 髪
    hat = look.hat
    full = hat in ('helmet', 'knight', 'ninja', 'hood')
    if hs != 'bald' and hs != 'none' and not full:
        cap = ellipse(-0.4, -0.7, rx + 0.3, ry + 0.4)
        fringe_y = -2.4 if hs not in ('spiky',) else -2.8
        region = union(rect(-99, -99, 99, fringe_y), rect(-99, -99, -2.2, 3.4 if hs != 'buzz' else 1.5),
                       poly([(-2.3, fringe_y), (1.5, fringe_y), (-2.3, 1.0)]))
        shp = inter(cap, region)
        if hs == 'side':  # 横分けの前髪
            shp = union(shp, poly([(1, -3), (6.5, -2.5), (4.5, 0.5)]))
        if hs in ('long', 'twin', 'braid', 'bob'):
            shp = union(shp, rrect(-rx - 0.4, -2, -0.6, 4.6, 1.5), poly([(2, -3), (6.8, -1.8), (6.6, 0.8), (4.5, -1.2)]))
        if hs == 'bob':
            shp = union(shp, rrect(-rx - 0.6, -3, 0.0, 5.0, 2.0))
        if hs == 'spiky':
            shp = union(shp, poly([(-7, -2), (-9.5, -5.5), (-5.5, -5.0), (-6, -9.5), (-2.5, -6.5), (-0.5, -10.5),
                                   (1.5, -6.8), (5.0, -8.5), (4.2, -4.8), (7.5, -3.0), (3.0, -2.0)]))
        if hs == 'bun':
            shp = union(shp, ellipse(-3.5, -6.6, 2.7, 2.5))
        if hs == 'afro':
            shp = union(ellipse(-1.6, -2.6, rx + 1.6, ry + 1.0), shp)
            shp = minus(shp, inter(union(rect(0.8, -2.6, 99, 99), rect(-1.0, 0.5, 99, 99)), ellipse(0, 0, rx, ry)))
        if hs == 'mohawk':
            shp = union(inter(cap, rect(-99, -99, 99, -4.0)), poly([(-5, -4), (-3, -10), (0, -10.5), (3, -8), (3, -4)]))
        if hs == 'twin':
            shp = union(shp, ellipse(-3.5, -6.0, 2.0, 1.8))
        cv.shape(shp, t, hairR)
    if look.beard:
        cv.shape(inter(ellipse(0.5, 1.0, rx + 0.4, ry + 1.6), union(rect(-1.5, 2.2, 99, 99), rect(4.5, 1.0, 99, 99))),
                 t, R(look.beard))
    # 顔
    if look.hat != 'knight':
        draw_face(cv, pal, look, t, eyes)
    # けもの耳
    if look.ears == 'cat':
        ec = R(look.ear_col if hasattr(look, 'ear_col') else look.hair)
        cv.shape(union(poly([(-5.5, -3.5), (-5.5, -9.5), (-1.5, -5.5)]), poly([(0, -6), (3.0, -9.5), (4.0, -4.2)])), t, ec)
    if look.ears == 'bunny':
        ec = R(look.hair)
        cv.shape(union(ellipse(-3.5, -10.5, 1.7, 4.6), ellipse(-0.5, -11, 1.7, 4.8)), t, ec)
    # 帽子
    if hat:
        draw_hat(cv, pal, look, t)


# 開いた目(見た目の eyes が 'normal' / 'big' のキャラクターに共通): 上まつげ + 白目 + 縦 3 ドットの黒目(右上に光)。
# (x, y, 色) の並び。色: 'e' = 黒目(eye_col があればその色) / 'q' = 白目・光 / 'k' = まつげ
OPEN_EYES = [(1.4, -1.0, 'k'), (2.4, -1.0, 'k'), (3.4, -1.0, 'k'), (1.4, 0.0, 'q'), (1.4, 1.0, 'q'),
             (2.4, 0.0, 'e'), (3.4, 0.0, 'q'), (2.4, 1.0, 'e'), (3.4, 1.0, 'e'), (2.4, 2.0, 'e'), (3.4, 2.0, 'e'),
             (5.4, -1.0, 'k'), (5.4, 0.0, 'e'), (5.4, 1.0, 'e'), (5.4, 2.0, 'e')]


def draw_face(cv, pal, look, t, eyes):
    ek = look.eyes
    e, q = 'e', 'q'
    if look.eye_col:
        e = pal.sym(look.eye_col)
    if ek in ('normal', 'big') and eyes != 'closed':
        for lx, ly, c in OPEN_EYES:
            cv.dot(t, lx, ly, {'e': e, 'q': q, 'k': 'e'}[c])
    elif eyes == 'closed' or ek == 'closed':
        for lx in (2.0, 3.0):
            cv.dot(t, lx, 1.2, 'e')
        cv.dot(t, 5.4, 1.2, 'e')
    elif ek == 'visor':
        cv.shape(rrect(1.0, -1.2, 7.0, 1.6, 0.9), t, pal.ramp(look.visor if hasattr(look, 'visor') else '#5ad2ff'), line=False)
    elif ek == 'glow':
        for lx, ly in ((2.2, 0), (2.2, 1), (5.2, 0), (5.2, 1)):
            cv.dot(t, lx, ly, pal.sym(look.eye_col or '#ff4040'))
    elif ek == 'sockets':  # がい骨
        for lx, ly in ((1.8, -0.5), (2.8, -0.5), (1.8, 0.5), (2.8, 0.5), (5.2, -0.5), (5.2, 0.5), (4.4, 2.6)):
            cv.dot(t, lx, ly, 'e')
    elif ek == 'alien':  # 大きな黒目(左上に光)
        for lx, ly in ((1.4, -1), (2.4, -1), (1.4, 0), (2.4, 0), (3.4, 0), (2.4, 1), (3.4, 1), (5.4, -1), (5.4, 0), (5.4, 1)):
            cv.dot(t, lx, ly, 'e')
        cv.dot(t, 1.4, -1, 'q')
    if look.glasses:
        gs = pal.sym(look.glasses)
        for lx, ly in ((1.4, -1), (3.4, -1), (1.4, 2), (3.4, 2), (1.4, 0), (1.4, 1), (3.4, 0), (3.4, 1), (4.4, -1),
                       (6.2, -1), (6.2, 0), (6.2, 1), (6.2, 2)):
            cv.dot(t, lx, ly, gs)
    if look.glasses_dark if hasattr(look, 'glasses_dark') else False:
        for lx, ly in ((1.5, 0), (2.5, 0), (3.5, 0), (4.5, 0), (5.5, 0), (2.5, 1), (5.5, 1), (1.5, 1), (3.5, 1)):
            cv.dot(t, lx, ly, 'e')
    if look.blush and ek not in ('sockets', 'visor'):
        cv.dot(t, 1.6, 2.6, pal.sym('#f4a6a0'))
    if look.mouth and ek not in ('sockets',) and not look.beard:
        cv.dot(t, 4.6, 3.4, pal.sym('#b0605a'))


def draw_hat(cv, pal, look, t):
    R = lambda c: pal.ramp(c)
    c1, c2 = R(look.hat_col), R(look.hat_col2)
    rx, ry = HEAD_R
    h = look.hat
    top = lambda y: inter(ellipse(-0.3, -0.6, rx + 0.7, ry + 0.7), rect(-99, -99, 99, y))
    if h == 'cap':
        cv.shape(top(-2.4), t, c1)
        cv.shape(rrect(2.0, -3.4, 10.2, -2.0, 0.7), t, c1)
    elif h == 'tophat':
        cv.shape(rect(-5.0, -15.0, 4.0, -4.0), t, c1)
        cv.shape(rect(-5.0, -6.6, 4.0, -5.2), t, c2, line=False)
        cv.shape(rrect(-7.6, -4.8, 6.6, -3.2, 0.8), t, c1)
    elif h == 'chef':
        cv.shape(union(ellipse(-0.6, -9.2, 6.0, 4.4), ellipse(-4, -7.5, 3.5, 3.5), ellipse(3, -7.5, 3.5, 3.5)), t, c1)
        cv.shape(rrect(-5.8, -6.2, 5.0, -2.4, 0.6), t, c1)
    elif h in ('helmet', 'knight'):
        cv.shape(ellipse(-0.3, -0.5, rx + 0.8, ry + 0.9), t, c1)
        cv.shape(rect(1.2, -0.6, 8.0, 0.9), t, pal.flat('#1d1620'), line=False, shade=False)
        cv.shape(inter(ellipse(-0.3, -0.5, rx + 0.8, ry + 0.9), union(rect(-0.8, -ry - 1, 0.6, ry), rect(-99, 2.4, 99, 2.9))), t, c1, line=True)
        if look.__dict__.get('plume'):
            cv.shape(union(ellipse(-3.5, -8.5, 3.6, 2.0), ellipse(-6.5, -6.5, 2.4, 2.4)), t, R(look.plume))
    elif h == 'crown':
        cv.shape(poly([(-5, -4.5), (5, -4.5), (5.5, -10), (3, -7.2), (0.5, -11), (-2, -7.2), (-4.6, -10)]), t, c1)
        cv.dot(t, 0.5, -6.0, pal.sym('#e0405a'))
    elif h in ('witch', 'wizard'):
        tall = 18 if h == 'wizard' else 16
        cv.shape(poly([(-6.2, -4.0), (5.6, -4.0), (0.5, -9.0), (-4.5, -tall + 1), (-6.5, -tall + 3), (-3.8, -10)]), t, c1)
        cv.shape(rect(-5.8, -5.8, 5.2, -4.2), t, c2, line=False)
        cv.shape(ellipse(-0.3, -3.8, 10.5, 1.6), t, c1)
        if h == 'wizard':
            cv.dot(t, -1.2, -9.0, pal.sym('#ffe066'))
            cv.dot(t, 1.5, -6.6, pal.sym('#ffe066'))
    elif h == 'cowboy':
        cv.shape(rrect(-5.2, -10.0, 4.2, -3.0, 2.2), t, c1)
        cv.shape(rect(-5.2, -5.0, 4.2, -3.8), t, c2, line=False)
        cv.shape(union(ellipse(-0.5, -3.3, 10.2, 1.6), ellipse(-9.5, -4.6, 1.4, 1.6), ellipse(8.5, -4.6, 1.4, 1.6)), t, c1)
    elif h == 'straw':
        cv.shape(rrect(-5.0, -8.5, 4.0, -3.0, 2.2), t, c1)
        cv.shape(rect(-5.0, -5.0, 4.0, -3.8), t, c2, line=False)
        cv.shape(ellipse(-0.5, -3.3, 10.5, 1.5), t, c1)
    elif h == 'ninja':
        cv.shape(minus(ellipse(-0.3, -0.4, rx + 0.6, ry + 0.6), rect(1.0, -1.3, 99, 1.8)), t, c1)
        cv.shape(union(capsule(-6.5, -1.5, -10, 1, 0.9), capsule(-6.5, -1.5, -10.5, -3, 0.9)), t, c1)
    elif h == 'hood':
        cv.shape(minus(ellipse(-0.6, -0.6, rx + 1.2, ry + 1.2), ellipse(2.4, 0.8, 4.6, 5.2)), t, c1)
    elif h == 'police':
        cv.shape(union(top(-2.6), rrect(-6.6, -8.2, 5.6, -3.0, 1.2)), t, c1)
        cv.shape(rect(-6.0, -4.4, 5.6, -2.8), t, R('#222831'), line=False)
        cv.shape(rrect(2.0, -3.4, 9.0, -2.0, 0.7), t, R('#222831'))
        cv.dot(t, 2.5, -6.0, pal.sym('#f0d050'))
    elif h == 'beret':
        cv.shape(union(ellipse(-1.2, -5.0, 7.4, 2.8), rect(-0.6, -8.6, 0.4, -7.0)), t, c1)
    elif h == 'headband':
        cv.shape(rect(-7, -3.6, 7, -1.8), t, c1)
        cv.shape(union(capsule(-6.6, -2.7, -10, -0.5, 0.8), capsule(-6.6, -2.7, -9.5, 2.5, 0.8)), t, c1)
    elif h == 'pirate':
        cv.shape(poly([(-9, -3.5), (8, -3.5), (5, -6.5), (0, -11), (-5, -6.5)]), t, c1)
        cv.dot(t, -0.5, -6.6, pal.sym('#f4f1ea'))
        cv.dot(t, -0.5, -5.6, pal.sym('#f4f1ea'))
    elif h == 'astro':
        cv.shape(minus(ellipse(0.3, -0.3, rx + 2.2, ry + 2.3), ellipse(0.9, -0.2, rx + 1.0, ry + 1.2)), t, c1)
        cv.dot(t, 3.5, -5.5, 'q')
        cv.dot(t, 4.5, -4.5, 'q')
    elif h == 'hardhat':
        cv.shape(top(-2.2), t, c1)
        cv.shape(rrect(-7.5, -3.2, 8.5, -1.8, 0.6), t, c1)
        cv.shape(rect(-0.6, -7.8, 0.6, -3.0), t, c2, line=False)
    elif h == 'santa':
        cv.shape(poly([(-6.4, -3.0), (5.6, -3.0), (2, -9), (-4, -11.5), (-8.5, -7.5)]), t, c1)
        cv.shape(rrect(-7.0, -4.4, 6.4, -2.0, 1.1), t, c2)
        cv.shape(ellipse(-9.0, -7.0, 1.8, 1.8), t, c2)
    elif h == 'nurse':
        cv.shape(poly([(-4.5, -4.5), (3.5, -4.5), (3.0, -8.0), (-4.0, -8.0)]), t, c1)
        cv.dot(t, -0.5, -6.8, pal.sym('#e0405a'))
        cv.dot(t, -0.5, -5.8, pal.sym('#e0405a'))
        cv.dot(t, -1.5, -6.3, pal.sym('#e0405a'))
        cv.dot(t, 0.5, -6.3, pal.sym('#e0405a'))
    elif h == 'fire':
        cv.shape(union(top(-2.0), poly([(-1, -7.5), (1, -7.5), (2, -4), (-2, -4)])), t, c1)
        cv.shape(union(rrect(-9.0, -2.8, 9.0, -1.2, 0.6)), t, c1)
        cv.dot(t, 3.0, -4.5, pal.sym('#f0d050'))
    elif h == 'horns':
        cv.shape(union(poly([(-3.5, -5), (-1.5, -5.5), (-3.0, -10)]), poly([(1.5, -5.6), (3.6, -5.0), (4.5, -9.5)])), t, c1)
    elif h == 'horn1':
        cv.shape(poly([(-1.5, -5.4), (1.5, -5.6), (0.2, -10.5)]), t, c1)
    elif h == 'antenna':
        cv.shape(union(rect(-1.0, -10, 0.0, -5), ellipse(-0.5, -10.5, 1.4, 1.4)), t, c1)
    elif h == 'antennae':
        cv.shape(union(capsule(-1.5, -5, -3.5, -10, 0.5), capsule(1.5, -5, 3.0, -10, 0.5),
                       ellipse(-3.5, -10.5, 1.3, 1.3), ellipse(3.0, -10.5, 1.3, 1.3)), t, c1)
    elif h == 'halo':
        cv.shape(minus(ellipse(-0.5, -9.5, 4.6, 1.5), ellipse(-0.5, -9.5, 3.0, 0.6)), t, c1, line=False)
    elif h == 'bandana':
        cv.shape(top(-2.0), t, c1)
        cv.shape(capsule(-6.4, -2.5, -9.5, 0.5, 1.0), t, c1)
    elif h == 'cat_hood':
        cv.shape(minus(ellipse(-0.6, -0.6, rx + 1.2, ry + 1.2), ellipse(2.4, 1.0, 4.8, 5.2)), t, c1)
        cv.shape(union(poly([(-5.5, -4.0), (-5.5, -10.0), (-1.5, -6.0)]), poly([(0, -6.5), (3.5, -10.0), (4.0, -4.4)])), t, c1)
    elif h == 'leaf':
        cv.shape(union(ellipse(1.0, -9.0, 3.4, 1.4), rect(-0.6, -8.0, 0.2, -5.6)), t, c1)
    elif h == 'flower':
        cv.shape(union(ellipse(-4.0, -5.0, 1.5, 1.5), ellipse(-2.0, -6.2, 1.5, 1.5), ellipse(-5.8, -6.3, 1.5, 1.5)), t, c1)
        cv.dot(t, -4.0, -5.8, pal.sym('#ffe066'))
    elif h == 'bow':
        cv.shape(union(ellipse(-5.5, -5.5, 2.0, 1.6), ellipse(-2.0, -6.8, 2.0, 1.6)), t, c1)
    elif h == 'sailor':
        cv.shape(union(rrect(-5.0, -8.0, 4.5, -3.2, 2.0), ellipse(-0.3, -3.5, 7.4, 1.4)), t, c1)
    elif h == 'grad':
        cv.shape(top(-3.0), t, c1)
        cv.shape(poly([(-8, -6.0), (0, -8.5), (8, -6.0), (0, -3.6)]), t, c1)
        cv.shape(capsule(0, -6.0, -6, -2, 0.5), t, R('#f0c040'), line=False)


def draw_item(cv, pal, look, arm, pose):
    """手前の手に持つ物"""
    (sx, sy), (ex, ey), (hx, hy), _, _ = arm
    R = lambda c: pal.ramp(c)
    ang = math.degrees(math.atan2(hx - ex, hy - ey))  # 前腕の向き(真下 = 0)
    it = look.item
    t = T(hx, hy, -ang)
    up = T(hx, hy, 0)
    if it == 'sword':
        cv.shape(rect(-0.6, 1.0, 0.6, 9.5), t, R('#d6dbe4'))
        cv.shape(rect(-2.0, 0.6, 2.0, 1.6), t, R('#c9a040'))
    elif it == 'staff':
        cv.shape(rect(-0.6, -9, 0.6, 6), up, R('#8a5a32'))
        cv.shape(ellipse(0, -10, 1.8, 1.8), up, R(look.item_col))
    elif it == 'wand':
        cv.shape(rect(-0.5, 1.0, 0.5, 6.0), t, R('#5a3a26'))
        cv.dot(t, 0, 6.5, pal.sym('#ffe066'))
    elif it == 'pan':
        cv.shape(union(rect(-0.5, 1.0, 0.5, 4.0), ellipse(0, 6.8, 2.8, 2.8)), t, R('#3a3f48'))
    elif it == 'bat':
        cv.shape(capsule(0, 1.0, 0, 10, 0.6, 1.2), t, R('#c89a5a'))
    elif it == 'trident':
        cv.shape(union(rect(-0.5, -9, 0.5, 6), rect(-2.2, -9, 2.2, -8), rect(-2.2, -11, -1.4, -8), rect(1.4, -11, 2.2, -8),
                       rect(-0.5, -12, 0.5, -8)), up, R(look.item_col))
    elif it == 'broom':
        cv.shape(rect(-0.5, -6, 0.5, 6), up, R('#8a5a32'))
        cv.shape(poly([(-1.8, 5.5), (1.8, 5.5), (2.8, 10.5), (-2.8, 10.5)]), up, R('#d8b050'))
    elif it == 'flag':
        cv.shape(rect(-0.4, -10, 0.4, 3), up, R('#8a8f99'))
        cv.shape(poly([(0.4, -10), (6.5, -8.5), (0.4, -6.5)]), up, R(look.item_col))
    elif it == 'mic':
        cv.shape(union(rect(-0.4, -3.0, 0.4, 0), ellipse(0, -3.6, 1.2, 1.2)), up, R('#3a3f48'))
    elif it == 'lantern':
        cv.shape(rrect(-1.6, 1.5, 1.6, 5.0, 0.6), t, R('#ffd060'))
    elif it == 'scythe':
        cv.shape(rect(-0.5, -10, 0.5, 6), up, R('#5a3a26'))
        cv.shape(poly([(0, -10), (8, -9), (10, -6), (6, -8), (0, -8.5)]), up, R('#c9ccd4'))
    elif it == 'brush':
        cv.shape(rect(-0.4, 1.0, 0.4, 6.0), t, R('#c89a5a'))
        cv.dot(t, 0, 6.5, pal.sym(look.item_col))
    elif it == 'ball':
        cv.shape(ellipse(1.5, 2.5, 2.2, 2.2), up, R(look.item_col))
    elif it == 'stick':
        cv.shape(rect(-0.5, -1.0, 0.5, 9.0), up, R('#8a5a32'))


def trim(g):
    """上の空の行を切り詰める(足元の位置は変わらない)"""
    cut = 0
    while cut < len(g) - 1 and all(c == '.' for c in g[cut]):
        cut += 1
    return g[cut:], cut


def frames(look_d):
    look = Look(look_d)
    pal = Palette(look.outline or '#2b2233')
    out = {}
    for name, pose in POSES.items():
        cv = draw(look, dict(pose, name=name), 36, 36 + TOP, pal=pal)
        g, cut = trim(cv.finish())
        out[name] = (g, 18, None)
    for name, pose in HANG.items():
        cv = draw(look, dict(pose, name=name), HANG_W, HANG_H + TOP, hang=pose, pal=pal)
        g, cut = trim(cv.finish())
        out[name] = (g, HANG_AX, pose['L'] + TOP - cut)
    return out, pal.colors
