import subprocess, sys, math, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = sys.argv[1]; OUT = sys.argv[2]; LOGO = sys.argv[3]
PREVIEW = [float(x) for x in sys.argv[4].split(',')] if len(sys.argv) > 4 else None
SW, SH = 1440, 2560; W, H = 1080, 1920; FPS = 30
SRC_DUR = 16.834; NSRC = int(round(SRC_DUR * FPS))
import timing as TM
OUT_DUR = TM.OLD_END
NOUT = int(round(TM.END * FPS))
GOLD = (255, 185, 46); WHITE = (255, 255, 255)
FD = '/usr/share/fonts/opentype/inter/'
BLACK = FD + 'InterDisplay-Black.otf'; XB = FD + 'InterDisplay-ExtraBold.otf'; SB = FD + 'Inter-SemiBold.otf'; BD = FD + 'Inter-Bold.otf'

def src_time(t):
    if t < 9.0: return t
    if t < 9.6: return 9.0 + (t - 9.0) * 2
    return min(t + 0.6, SRC_DUR - 1 / FPS)

# ---------- easing ----------
def clamp(x, a=0, b=1): return max(a, min(b, x))
def eo_cubic(p): p = clamp(p); return 1 - (1 - p) ** 3
def ei_cubic(p): p = clamp(p); return p ** 3
def eo_back(p, s=1.9): p = clamp(p) - 1; return 1 + p * p * ((s + 1) * p + s)
def lerp(a, b, p): return a + (b - a) * p

# ---------- camera ----------
def punch(t, t0, amt, dur=0.3):
    if t < t0 or t > t0 + dur: return 0
    return amt * (1 - eo_cubic((t - t0) / dur))

def camera(t):
    """returns zoom, blur_strength(0-1 zoom blur), dx, dy"""
    blur = 0; dx = dy = 0
    if t < 0.4: z = lerp(1.15, 1.04, eo_cubic(t / 0.4))
    elif t < 2.5: z = lerp(1.04, 1.08, (t - 0.4) / 2.1)
    elif t < 2.733: p = (t - 2.5) / 0.233; z = lerp(1.08, 1.32, ei_cubic(p)); blur = p
    elif t < 3.0: p = (t - 2.733) / 0.267; z = lerp(1.25, 1.0, eo_cubic(p)); blur = 1 - p
    elif t < 5.8: z = lerp(1.0, 1.08, (t - 3.0) / 2.8)
    elif t < 13.3: z = lerp(1.04, 1.09, (t - 5.8) / 7.5)
    elif t < 13.567: p = (t - 13.3) / 0.267; z = lerp(1.09, 1.32, ei_cubic(p)); blur = p; dy = -160 * ei_cubic(p)
    elif t < 13.85: p = (t - 13.567) / 0.283; z = lerp(1.22, 1.0, eo_cubic(p)); blur = 1 - p
    else: z = lerp(1.0, 1.045, (t - 13.85) / (OUT_DUR - 13.85))
    if 5.75 < t < 5.8: z = 1.04
    for bt in TM.BEAT_PUNCH: z += punch(t, TM.old_of_new(bt), 0.03, 0.25)
    z += punch(t, 6.3, 0.06) + punch(t, 8.2, 0.06) + punch(t, 10.4, 0.10, 0.35)
    if t < 0.1 or 10.85 <= t < 10.92:
        rnd = random.Random(int(t * 1000)); dx += rnd.uniform(-14, 14); dy += rnd.uniform(-14, 14)
    return z, blur, dx, dy

def warp(frame, z, dx, dy):
    s = z * W / SW
    M = np.array([[s, 0, W / 2 - s * SW / 2 + dx], [0, s, H / 2 - s * SH / 2 + dy]], dtype=np.float32)
    return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def render_bg(frame, t):
    z, blur, dx, dy = camera(t)
    if blur > 0.02:
        n = 7; acc = np.zeros((H, W, 3), np.float32)
        for i in range(n):
            acc += warp(frame, z * (1 + 0.09 * blur * i / (n - 1)), dx, dy)
        out = (acc / n).astype(np.uint8)
    else:
        out = warp(frame, z, dx, dy)
    # CTA treatment: blur + darken
    if t >= 13.85:
        p = eo_cubic((t - 13.85) / 0.5)
        sig = 9 * p
        if sig > 0.3: out = cv2.GaussianBlur(out, (0, 0), sig)
        out = (out.astype(np.float32) * (1 - 0.3 * p)).astype(np.uint8)
    out = out.astype(np.float32)
    # vignette always (subtle), stronger on CTA
    out *= VIG
    # flashes
    for t0, a0, d in [(0.0, 0.85, 0.1), (2.733, 0.35, 0.1), (10.4, 0.25, 0.1)]:
        if t0 <= t < t0 + d:
            a = a0 * (1 - (t - t0) / d); out = out * (1 - a) + 255 * a
    return np.clip(out, 0, 255).astype(np.uint8)

yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIG = (1 - 0.28 * np.clip(r - 0.55, 0, 1) ** 1.5)[..., None].astype(np.float32)


# ---------- storyboard layers (rendered by Chromium with Montserrat, exact storyboard CSS) ----------
import json
META = json.load(open('layers/meta.json'))
L = {}
def layer(i):
    if i in L: return L[i]
    im = Image.open(f'layers/{i}.png').convert('RGBA')
    bb = im.getchannel('A').getbbox()
    crop = im.crop(bb)
    tx, ty, tw, th = META[i]['text'] if i in META else (0, 0, W, H)
    L[i] = (crop, bb, (tx + tw / 2, ty + th / 2), META.get(i, {}).get('text'))
    return L[i]
def safe_comp(canvas, im, px, py):
    l, t = max(0, px), max(0, py); r_, b = min(W, px + im.width), min(H, py + im.height)
    if r_ <= l or b <= t: return
    canvas.alpha_composite(im.crop((l - px, t - py, r_ - px, b - py)), (l, t))
def with_alpha(im, a):
    if a >= 0.999: return im
    arr = np.array(im); arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')
def put(canvas, im, bb, ctr, sc=1, al=1, dx=0, dy=0):
    if al <= 0.01 or sc <= 0.01: return
    cx, cy = ctr; x0, y0 = bb[0], bb[1]
    if abs(sc - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
        x0 = cx + (x0 - cx) * sc; y0 = cy + (y0 - cy) * sc
    safe_comp(canvas, with_alpha(im, al), int(x0 + dx), int(y0 + dy))

E = []
def el(i, t_in, t_out, anim='fade', out='fade', **k): E.append(dict(id=i, t_in=t_in, t_out=t_out, anim=anim, out=out, **k))
el('h1', 0.05, 1.45, 'slam'); el('h2', 0.38, 1.45, 'slam'); el('h3', 0.75, 1.45, 'slam')
el('b1', 1.55, 2.6, 'type'); el('b2', 1.98, 2.6, 'rise')
el('r1', 3.05, 5.65); el('r2', 2.85, 5.65, 'pop', sweep=(3.3, 3.85)); el('r3', 3.25, 5.65)
el('c1', 6.3, 8.2, 'pop', 'flipout'); el('c2', 8.2, 10.4, 'flipin', 'flipout'); el('c3', 10.4, 12.15, 'pop', glow=True)
el('f1', 10.65, 12.15); el('f2', 10.85, 12.15, 'stamp')
for n in range(4): el(f'l{n+1}', 12.2 + n * 0.13, 13.35, 'slide')
CTA = 13.95
el('grad', CTA - 0.1, 99, 'fadeonly')
el('k1', CTA, 99); el('k2', CTA + 0.3, 99, 'rise'); el('k3', CTA + 0.6, 99); el('k4', CTA + 0.72, 99)
el('k5', CTA + 0.9, 99, 'slam', pulse=True); el('k6', CTA + 1.05, 99, 'slam', pulse=True)

for e in E:
    if e['id'] in TM.OVR:
        d = e['t_in'] - TM.old_of_new(TM.OVR[e['id']]); e['t_in'] -= d
        if e['t_out'] < 90 and e['id'] not in TM.OUT_OVR and e['id'][0] in 'k': e['t_out'] -= d
    if e['id'] in TM.OUT_OVR: e['t_out'] = TM.old_of_new(TM.OUT_OVR[e['id']])
    if e['id'] == 'grad': e['t_in'] = TM.old_of_new(14.0)
F2_IN = TM.old_of_new(TM.OVR['f2'])
def sweep(im, p):
    arr = np.array(im).astype(np.float32); a = arr[..., 3] / 255
    ga = np.clip((a - 0.6) / 0.4, 0, 1)
    h_, w_ = a.shape
    x = np.arange(w_)[None, :] + np.arange(h_)[:, None] * 0.35
    c = lerp(-0.3 * w_, 1.5 * w_, p)
    m = (np.exp(-((x - c) / (w_ * 0.07)) ** 2) * 0.85 * ga)[..., None]
    arr[..., :3] = arr[..., :3] * (1 - m) + 255 * m
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')
_glow = {}
def glow_of(i, im):
    if i not in _glow:
        a = np.array(im)[..., 3].astype(np.float32) / 255
        pad = 80; A = np.pad(a, pad)
        g = np.clip(cv2.GaussianBlur(A, (0, 0), 30) * 1.4, 0, 1) * 0.75
        arr = np.zeros(g.shape + (4,), np.uint8); arr[..., 0], arr[..., 1], arr[..., 2] = GOLD; arr[..., 3] = (g * 255).astype(np.uint8)
        _glow[i] = (Image.fromarray(arr, 'RGBA'), pad)
    return _glow[i]

def sparkles(canvas, t, t0, cx, cy):
    if t < t0 or t > t0 + 0.9: return
    d = ImageDraw.Draw(canvas); rnd = random.Random(7)
    for n in range(9):
        ang = rnd.uniform(0, 2 * math.pi); rad = rnd.uniform(300, 470)
        px = cx + math.cos(ang) * rad; py = cy + math.sin(ang) * rad * 0.42
        ph = (t - t0 - n * 0.05) / 0.5
        if not 0 < ph < 1: continue
        s = math.sin(ph * math.pi) * rnd.uniform(14, 28)
        pts = [(px, py - s * 2), (px + s * .35, py - s * .35), (px + s * 2, py), (px + s * .35, py + s * .35),
               (px, py + s * 2), (px - s * .35, py + s * .35), (px - s * 2, py), (px - s * .35, py - s * .35)]
        d.polygon(pts, fill=GOLD + (230,))

def draw_elements(canvas, t):
    for e in E:
        if t < e['t_in'] or t > e['t_out'] + 0.2: continue
        im, bb, ctr, tr = layer(e['id']); bb = list(bb)
        sc = 1; al = 1; dx = dy = 0; lt = t - e['t_in']; an = e['anim']
        if an == 'slam': sc = lerp(1.45, 1, eo_back(lt / 0.2, 2.2)); al = clamp(lt / 0.07)
        elif an == 'pop': sc = eo_back(lt / 0.28, 2.0); al = clamp(lt / 0.06)
        elif an == 'stamp': sc = lerp(2.1, 1, eo_cubic(lt / 0.16)); al = clamp(lt / 0.05)
        elif an == 'fade': sc = lerp(0.9, 1, eo_cubic(lt / 0.3)); al = clamp(lt / 0.25)
        elif an == 'fadeonly': al = clamp(lt / 0.5)
        elif an == 'slide': dx = -320 * (1 - eo_cubic(lt / 0.28)); al = clamp(lt / 0.18)
        elif an == 'flipin': dy = 120 * (1 - eo_back(lt / 0.22)); al = clamp(lt / 0.12)
        elif an == 'type':
            p = clamp(lt / 0.4); edge = tr[0] + tr[2] * p - bb[0] + 40  # wipe left->right through text box
            if edge <= 0: continue
            im = im.crop((0, 0, int(min(im.width, edge)), im.height))
        elif an == 'rise':
            p = eo_cubic(lt / 0.3); bottom = tr[1] + tr[3] + 30 - bb[1]
            off = (1 - p) * (tr[3] + 30)
            arr = np.array(im); full = Image.new('RGBA', im.size, (0, 0, 0, 0))
            shifted = Image.new('RGBA', im.size, (0, 0, 0, 0)); shifted.alpha_composite(im, (0, int(off)) if off < im.height else (0, 0))
            # mask everything below the text baseline (the "floor" the text rises from)
            m = np.array(shifted); m[int(bottom):, :, 3] = 0; im = Image.fromarray(m, 'RGBA')
            if off >= im.height: continue
        if e.get('sweep'):
            s0, s1 = e['sweep']
            if s0 <= t <= s1: im = sweep(im, (t - s0) / (s1 - s0))
        if e.get('pulse') and lt > 0.4: sc *= 1 + 0.035 * (0.5 - 0.5 * math.cos((lt - 0.4) * 2 * math.pi / 0.9))
        ot = t - e['t_out']
        if ot > 0:
            if e['out'] == 'flipout': dy -= 120 * eo_cubic(ot / 0.18); al *= 1 - clamp(ot / 0.15)
            else: sc *= lerp(1, 1.12, eo_cubic(ot / 0.18)); al *= 1 - clamp(ot / 0.15)
        if e.get('glow'):
            g, pad = glow_of(e['id'], im)
            gp = 0.6 + 0.4 * math.exp(-lt * 3)
            put(canvas, g, (bb[0] - pad, bb[1] - pad), ctr, sc, al * gp, dx, dy)
        put(canvas, im, bb, ctr, sc, al, dx, dy)
    c = layer('f2')[2]; sparkles(canvas, t, F2_IN + 0.05, c[0], c[1])

def frames():
    cmd = ['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    sz = SW * SH * 3
    while True:
        b = p.stdout.read(sz)
        if len(b) < sz: break
        yield np.frombuffer(b, np.uint8).reshape(SH, SW, 3)

def main():
    times = [k / FPS for k in range(NOUT)] if PREVIEW is None else PREVIEW
    if PREVIEW is None:
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    gen = frames(); cur_i = -1; cur = None
    for k, t in enumerate(times):
        si = min(int(round(TM.src_of_new(t) * FPS)), NSRC - 1)
        tn = t; t = TM.old_of_new(tn)
        while cur_i < si:
            try: cur = next(gen); cur_i += 1
            except StopIteration: break
        bg = render_bg(cur, t)
        canvas = Image.fromarray(bg).convert('RGBA')
        draw_elements(canvas, t)
        rgb = canvas.convert('RGB')
        if PREVIEW is None: enc.stdin.write(rgb.tobytes())
        else: rgb.resize((360, 640)).save(f'{OUT}_{tn:05.2f}.jpg', quality=85)
        if k % 60 == 0: print('frame', k, flush=True)
    if PREVIEW is None: enc.stdin.close(); enc.wait()

main()
