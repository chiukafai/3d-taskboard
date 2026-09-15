// 可靠取图：渲染到 WebGLRenderTarget → readRenderTargetPixels → 自写 PNG
// 为什么不用 page.screenshot()/canvas.toDataURL()：看板 renderer 用 {alpha:true} 且未开
// preserveDrawingBuffer，无 GPU 沙箱里默认帧缓冲读回恒为空（曾经由此产生大量"空白伪影"）。
import zlib from 'node:zlib';
import fs from 'node:fs';

let _tbl = null;
function crcTable() {
  if (_tbl) return _tbl;
  _tbl = new Int32Array(256);
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; _tbl[n] = c; }
  return _tbl;
}
function crc32(buf) { const t = crcTable(); let c = -1; for (let i = 0; i < buf.length; i++) c = t[(c ^ buf[i]) & 0xff] ^ (c >>> 8); return (c ^ -1) >>> 0; }
function chunk(type, data) {
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
  const t = Buffer.from(type, 'ascii');
  const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(Buffer.concat([t, data])));
  return Buffer.concat([len, t, data, crc]);
}
export function encodePNG(width, height, rgbaTopDown) {
  const stride = width * 4;
  const raw = Buffer.alloc((stride + 1) * height);
  for (let y = 0; y < height; y++) {
    raw[y * (stride + 1)] = 0;
    Buffer.from(rgbaTopDown.buffer, rgbaTopDown.byteOffset + y * stride, stride).copy(raw, y * (stride + 1) + 1);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0); ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', zlib.deflateSync(raw, { level: 6 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

/** 把当前场景渲染进离屏 RT 并落盘为 PNG（不依赖默认帧缓冲） */
export async function rtShot(page, file, W = 1280, H = 900, bg = 0xf4f1eb) {
  const b64 = await page.evaluate(async ([W, H, bg]) => {
    const THREE = await import('three');
    const d = window.__boardDebug;
    if (!d.__rt || d.__rt.width !== W) {
      if (d.__rt) d.__rt.dispose();
      d.__rt = new THREE.WebGLRenderTarget(W, H, { samples: 0 });
    }
    const rt = d.__rt, r = d.renderer;
    const prevT = r.getRenderTarget(), prevA = r.getClearAlpha(), prevC = new THREE.Color(); r.getClearColor(prevC);
    r.setRenderTarget(rt);
    r.setClearColor(bg, 1);
    r.clear();
    r.render(d.scene, d.camera);
    const buf = new Uint8Array(W * H * 4);
    r.readRenderTargetPixels(rt, 0, 0, W, H, buf);
    r.setRenderTarget(prevT);
    r.setClearColor(prevC, prevA);
    // GL 是自下而上 → 翻成自上而下
    const out = new Uint8Array(W * H * 4);
    for (let y = 0; y < H; y++) out.set(buf.subarray((H - 1 - y) * W * 4, (H - y) * W * 4), y * W * 4);
    let s = ''; const CH = 32768;
    for (let i = 0; i < out.length; i += CH) s += String.fromCharCode.apply(null, out.subarray(i, i + CH));
    return btoa(s);
  }, [W, H, bg]);
  fs.writeFileSync(file, encodePNG(W, H, Buffer.from(b64, 'base64')));
  return file;
}
export async function look(page, px, py, pz, lx, ly, lz) {
  await page.evaluate(([px, py, pz, lx, ly, lz]) => {
    const d = window.__boardDebug;
    d.scene.fog = null;
    d.controls.enableDamping = false;
    d.controls.minDistance = 0.05;   // 关键：默认 minDistance=9 会把近景相机顶开
    d.controls.maxDistance = 200;
    d.controls.minPolarAngle = 0;
    d.controls.maxPolarAngle = Math.PI;
    d.camera.position.set(px, py, pz);
    d.controls.target.set(lx, ly, lz);
    d.camera.lookAt(lx, ly, lz);
    d.controls.update();
    d.camera.updateMatrixWorld(true);
  }, [px, py, pz, lx, ly, lz]);
  await page.waitForTimeout(200);
}
