"""Build stl/parts.html: a single offline page that previews every printable part in 3D,
with quantity, material, print settings and size. The meshes are embedded (indexed,
gzipped, base64) so it works straight out of the zip with no internet.

    python tools/make_parts_html.py          (run after cad/skycrawler.py)
"""
import base64, gzip, json, os, struct
import numpy as np
import trimesh

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
STL = os.path.join(ROOT, 'stl')
BUNDLE = os.path.join(ROOT, 'tools', 'parts_viewer', 'parts_viewer.bundle.js')

PARTS = [  # file, title, qty, material, colour, settings, what it does
    ('chassis_bottom', 'Bottom plate', '1', 'PETG / ASA', '#3a3e46', '3 walls · 30 % gyroid · no supports',
     'Holds the four hip servos, the deck pillars and the battery straps.'),
    ('chassis_deck', 'Deck', '1', 'PETG / ASA', '#3a3e46', '3 walls · 30 % · no supports',
     'Top plate: bushings for the hip pins, 20×20 flight-controller standoffs, ESP32 bay.'),
    ('canopy', 'Canopy', '1', 'PETG / PLA (any colour)', '#e9e8e3', '2 walls · 10 % · tree supports under the roof',
     'Shell over the electronics with hex and side vents and a USB-C slot at the front.'),
    ('coxa', 'Upper leg (coxa)', '4', 'PETG / ASA', '#3a3e46', '4 walls · 40 % · supports for the knee frame and stop ledge',
     'Bolts to the hip servo horn; its pin turns in the deck. Holds the knee servo and the end stop (magnet + M3 levelling screw).'),
    ('shin_arm', 'Lower leg / drone arm', '4', 'PETG / ASA', '#3a3e46', '4 walls · 40 % · prints upside down (motor seat on the bed) · tree supports under the arm and tail',
     'Leg when walking, arm when flying. Slotted motor mount fits any 1103-1404 motor (9 mm circle, 9×9, 12×12); the toe is the landing gear.'),
    ('foot_tpu', 'Foot boot', '4', 'TPU 95A', '#ff6b1a', '2 walls · 20 %',
     'Slips over each toe: grip for walking, cushion for landing.'),
    ('leg_spacer', 'Horn spacer (optional)', '0–4', 'Any', '#8a8f99', '100 %',
     'Only if a servo horn sits below flush in its pocket.'),
]


def pack(path):
    m = trimesh.load(path)
    v = np.round(m.vertices.astype(np.float32), 3)
    f = m.faces.astype(np.uint32).ravel()
    raw = struct.pack('<II', len(v), len(f)) + v.astype('<f4').tobytes() + f.astype('<u4').tobytes()
    ext = m.extents
    return (base64.b64encode(gzip.compress(raw, 9)).decode(),
            [round(float(x), 1) for x in ext], round(float(m.volume) / 1000, 1))


def main():
    parts, total_g = [], 0.0
    for (f, title, qty, mat, col, settings, note) in PARTS:
        data, dims, vol = pack(os.path.join(STL, f + '.stl'))
        dens = 1.21 if 'TPU' in mat else 1.27
        grams = vol * dens * 0.55          # walls + infill: a rough fraction of solid
        n = 1 if qty == '0–4' else int(qty)
        if qty != '0–4':
            total_g += grams * n
        parts.append(dict(file=f, title=title, qty=qty, mat=mat, col=col, settings=settings, note=note,
                          dims=dims, vol=vol, grams=round(grams), data=data))
    html = TEMPLATE.replace('/*BUNDLE*/', open(BUNDLE).read()).replace('/*PARTS*/', json.dumps(parts)) \
                   .replace('/*TOTAL*/', str(round(total_g / 5) * 5))
    json.dump([{k: v for k, v in p.items() if k != 'data'} for p in parts],
              open(os.path.join(ROOT, 'tools', 'printed_parts.json'), 'w'), indent=1, ensure_ascii=False)
    out = os.path.join(STL, 'parts.html')
    open(out, 'w').write(html)
    print('wrote', out, round(os.path.getsize(out) / 1e6, 2), 'MB')


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SkyCrawler — printable parts</title>
<style>
*{box-sizing:border-box} html,body{margin:0;height:100%;background:#16181d;color:#e9ecf2;font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
#app{display:grid;grid-template-columns:300px 1fr;height:100%}
aside{overflow:auto;padding:18px 14px;border-right:1px solid #262a32;background:#121418}
h1{font-size:18px;margin:0 2px 2px} .sub{color:#8d96a6;font-size:12px;margin:0 2px 14px}
.card{display:flex;gap:10px;align-items:center;padding:10px;border-radius:10px;cursor:pointer;border:1px solid transparent;margin-bottom:6px}
.card:hover{background:#1c1f26} .card.on{background:#20242c;border-color:#ff6b1a}
.sw{width:14px;height:14px;border-radius:4px;flex:none;border:1px solid #0006}
.card b{display:block;font-weight:600} .card small{color:#8d96a6}
.qty{margin-left:auto;font-weight:700;color:#ff6b1a;font-size:13px}
.tot{margin:14px 2px 0;padding-top:12px;border-top:1px solid #262a32;color:#8d96a6;font-size:12px}
main{position:relative;overflow:hidden;background:radial-gradient(120% 90% at 50% 30%,#323743 0%,#1d2027 60%,#14161b 100%)}
canvas{display:block}
#info{position:absolute;right:16px;top:16px;width:310px;padding:14px 16px;border-radius:14px;background:rgba(14,16,20,.72);backdrop-filter:blur(8px);border:1px solid #ffffff14}
#info h2{margin:0 0 4px;font-size:17px} #info p{margin:6px 0;color:#c3c9d4}
.kv{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:10px 0;font-size:13px} .kv span:nth-child(odd){color:#8d96a6}
a.btn{display:inline-block;margin:6px 6px 0 0;padding:7px 12px;border-radius:8px;background:#ff6b1a;color:#111;font-weight:600;text-decoration:none}
a.btn.alt{background:#2a2e37;color:#e9ecf2}
#hint{position:absolute;left:16px;bottom:12px;color:#8d96a6;font-size:12px}
@media (max-width:760px){#app{grid-template-columns:1fr;grid-template-rows:auto 1fr} aside{display:flex;gap:6px;overflow-x:auto;border:0;padding:10px}
 h1,.sub,.tot{display:none} .card{flex:none} #info{left:10px;right:10px;top:auto;bottom:10px;width:auto}}
</style></head><body>
<div id="app">
<aside><h1>SkyCrawler parts</h1><p class="sub">Every file here is already oriented flat for printing.</p><div id="list"></div>
<p class="tot">Filament for one robot ≈ <b>/*TOTAL*/ g</b> (rough, at the settings shown).<br>Files open in any slicer: drag the .stl in.</p></aside>
<main id="view"><div id="info"></div><div id="hint">Drag to rotate · scroll to zoom · ↑/↓ for the next part · grid = 10 mm</div></main>
</div>
<script>/*BUNDLE*/</script>
<script>
const PARTS = /*PARTS*/;
const { THREE, OrbitControls, RoomEnvironment, toCreasedNormals } = window.SkyParts;
const view = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
view.prepend(renderer.domElement);
const scene = new THREE.Scene();
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.6;
const cam = new THREE.PerspectiveCamera(32, 1, 1, 5000); cam.up.set(0, 0, 1);
const ctl = new OrbitControls(cam, renderer.domElement); ctl.enableDamping = true;
const key = new THREE.DirectionalLight(0xfff1e0, 2.2); key.position.set(-120, -160, 300); key.castShadow = true;
Object.assign(key.shadow.camera, { left: -150, right: 150, top: 150, bottom: -150 }); key.shadow.mapSize.set(2048, 2048); key.shadow.radius = 5; scene.add(key);
const rim = new THREE.DirectionalLight(0x9cc4ff, 1.3); rim.position.set(160, 200, 120); scene.add(rim);
// print bed: plate + 10 mm grid
const bed = new THREE.Mesh(new THREE.PlaneGeometry(220, 220), new THREE.MeshStandardMaterial({ color: 0x23262d, roughness: 0.85 }));
bed.receiveShadow = true; bed.position.z = -0.05; scene.add(bed);
const grid = new THREE.GridHelper(220, 22, 0x4a505c, 0x30343d); grid.rotation.x = Math.PI / 2; scene.add(grid);

async function decode(b64) {
  const bin = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const buf = await new Response(new Blob([bin]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  const [nv, ni] = new Uint32Array(buf, 0, 2);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buf, 8, nv * 3), 3));
  g.setIndex(new THREE.BufferAttribute(new Uint32Array(buf, 8 + nv * 12, ni), 1));
  return toCreasedNormals(g, 32 * Math.PI / 180);
}
const cache = {}; let current = null, idx = 0;
const list = document.getElementById('list'), info = document.getElementById('info');
PARTS.forEach((p, i) => {
  const c = document.createElement('div'); c.className = 'card';
  c.innerHTML = `<span class="sw" style="background:${p.col}"></span><div><b>${p.title}</b><small>${p.mat}</small></div><span class="qty">×${p.qty}</span>`;
  c.onclick = () => show(i); list.appendChild(c);
});
async function show(i) {
  idx = (i + PARTS.length) % PARTS.length; const p = PARTS[idx];
  [...list.children].forEach((c, j) => c.classList.toggle('on', j === idx));
  info.innerHTML = `<h2>${p.title}</h2><p>${p.note}</p>
    <div class="kv"><span>Print</span><span>×${p.qty}</span><span>Material</span><span>${p.mat}</span>
    <span>Settings</span><span>${p.settings}</span><span>Size</span><span>${p.dims.join(' × ')} mm</span>
    <span>Solid volume</span><span>${p.vol} cm³ (≈ ${p.grams} g each)</span></div>
    <a class="btn" href="${p.file}.stl" download>Download STL</a><a class="btn alt" href="${p.file}.step" download>STEP</a>`;
  if (!cache[p.file]) {
    const m = new THREE.Mesh(await decode(p.data), new THREE.MeshPhysicalMaterial({ color: p.col, roughness: 0.55, clearcoat: 0.15 }));
    m.castShadow = m.receiveShadow = true; cache[p.file] = m;
  }
  if (current) scene.remove(current);
  current = cache[p.file]; scene.add(current);
  const s = Math.max(...p.dims), zc = p.dims[2] / 2;
  cam.position.set(s * 1.5, -s * 1.9, s * 1.35 + zc); ctl.target.set(0, 0, zc); ctl.update();
}
addEventListener('keydown', (e) => { if (e.key === 'ArrowDown' || e.key === 'ArrowRight') show(idx + 1); if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') show(idx - 1); });
function size() { const r = view.getBoundingClientRect(); renderer.setSize(r.width, r.height); cam.aspect = r.width / r.height; cam.updateProjectionMatrix(); }
addEventListener('resize', size); size();
renderer.setAnimationLoop(() => { ctl.update(); renderer.render(scene, cam); });
show(0);
window.showPart = show;
</script></body></html>'''

if __name__ == '__main__':
    main()
