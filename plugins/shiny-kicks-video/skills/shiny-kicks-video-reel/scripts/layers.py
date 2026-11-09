import json, os
from playwright.sync_api import sync_playwright
F = '/home/claude/sk/fonts/package/files/'
CSS = f"""
@font-face{{font-family:Montserrat;font-weight:600;src:url(file://{F}montserrat-latin-600-normal.woff2)}}
@font-face{{font-family:Montserrat;font-weight:900;src:url(file://{F}montserrat-latin-900-normal.woff2)}}
html,body{{margin:0;background:transparent}}
.frame{{position:relative;width:1080px;height:1920px;container-type:inline-size;font-family:Montserrat,Helvetica,Arial,sans-serif}}
.ov{{position:absolute;inset:0;display:none;flex-direction:column;padding:9cqw;gap:2cqw;box-sizing:border-box}}
.ov.on{{display:flex}}
.t{{font-weight:900;line-height:.95;text-transform:uppercase;text-shadow:0 10px 49px rgba(0,0,0,.55);letter-spacing:-.01em}}
.w{{color:#fff}}.g{{color:#FFB92E}}
.s{{font-weight:600;font-size:6.5cqw;color:#fff;text-shadow:0 5px 39px rgba(0,0,0,.7)}}
"""
# exact overlay markup from the approved storyboard (ids added)
SC = {
 's1': ('justify-content:center', '<div id="h1" class="t w" style="font-size:15cqw">¿Tienes</div><div id="h2" class="t g" style="font-size:24cqw">3 pares</div><div id="h3" class="t w" style="font-size:15cqw">sucios?</div>'),
 's2': ('justify-content:flex-end;padding-bottom:20cqw', '<div id="b1" class="s">Los sábados</div><div id="b2" class="t w" style="font-size:16cqw">cambian</div>'),
 's3': ('justify-content:center;align-items:center;text-align:center', '<div id="r1" class="s">Todos los sábados</div><div id="r2" class="t g" style="font-size:42cqw;line-height:.85">3x2</div><div id="r3" class="s">en limpieza</div>'),
 's4': ('justify-content:flex-start;align-items:flex-end', '<div id="c1" class="t g" style="font-size:40cqw">1</div>'),
 's5': ('justify-content:flex-start;align-items:flex-end', '<div id="c2" class="t g" style="font-size:40cqw">2</div>'),
 's6': ('justify-content:space-between', '<div id="c3" class="t g" style="font-size:40cqw;align-self:flex-end">3</div><div><div id="f1" class="s">el más barato</div><div id="f2" class="t w" style="font-size:20cqw">¡gratis!</div></div>'),
 's7': ('justify-content:center;gap:1cqw', '<div id="l1" class="t w" style="font-size:12cqw">Tenis</div><div id="l2" class="t w" style="font-size:12cqw">Gorras</div><div id="l3" class="t w" style="font-size:12cqw">Botas</div><div id="l4" class="t g" style="font-size:12cqw">Calzado formal</div>'),
 's8': ('justify-content:center;align-items:center;text-align:center', '<div id="k1" class="t w" style="font-size:9cqw">Shiny Kicks</div><div id="k2" class="t g" style="font-size:13cqw">Este sábado</div><div id="k3" class="s">10:00 – 14:00 h</div><div id="k4" class="s">Metepec · Toluca</div><div id="k5" class="t w" style="font-size:9.5cqw;margin-top:4cqw">Cotiza por WhatsApp ↓</div><div id="k6" class="t g" style="font-size:9.5cqw">729 157 9406</div>'),
}
html = f"<style>{CSS}</style><div class='frame'>" + ''.join(
    f"<div class='ov' id='{k}' style='{st}'>{inner}</div>" for k, (st, inner) in SC.items()) + \
    "<div id='grad' style='position:absolute;inset:0;display:none;background:linear-gradient(transparent 30%,rgba(0,0,0,.55))'></div></div>"
os.makedirs('/home/claude/sk/layers', exist_ok=True)
open('/home/claude/sk/layers/page.html', 'w').write(html)
meta = {}
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    pg.goto('file:///home/claude/sk/layers/page.html'); pg.wait_for_timeout(300)
    pg.evaluate("document.fonts.ready")
    for k in SC:
        pg.evaluate(f"document.querySelectorAll('.ov').forEach(e=>e.classList.remove('on'));document.getElementById('{k}').classList.add('on')")
        ids = pg.evaluate(f"[...document.querySelectorAll('#{k} [id]')].map(e=>e.id)")
        for i in ids:
            pg.evaluate(f"document.querySelectorAll('#{k} [id]').forEach(e=>e.style.visibility=(e.id=='{i}'?'visible':'hidden'))")
            r = pg.evaluate(f"(()=>{{const r=document.getElementById('{i}').getBoundingClientRect();return [r.x,r.y,r.width,r.height]}})()")
            # tight text box (for center of animations)
            tr = pg.evaluate(f"(()=>{{const e=document.getElementById('{i}');const rg=document.createRange();rg.selectNodeContents(e);const r=rg.getBoundingClientRect();return [r.x,r.y,r.width,r.height]}})()")
            pg.screenshot(path=f'/home/claude/sk/layers/{i}.png', omit_background=True)
            meta[i] = {'box': r, 'text': tr}
    pg.evaluate("document.querySelectorAll('.ov').forEach(e=>e.classList.remove('on'));document.getElementById('grad').style.display='block'")
    pg.screenshot(path='/home/claude/sk/layers/grad.png', omit_background=True)
    fam = pg.evaluate("document.fonts.check('900 50px Montserrat')")
    b.close()
json.dump(meta, open('/home/claude/sk/layers/meta.json', 'w'), indent=1)
print('font ok:', fam, len(meta))
