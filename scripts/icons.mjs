import { deflateSync } from "node:zlib";
import { writeFile } from "node:fs/promises";
function crc(buffer) {
  let c = 0xffffffff;
  for (const n of buffer) {
    c ^= n;
    for (let i = 0; i < 8; i++) c = (c >>> 1) ^ (c & 1 ? 0xedb88320 : 0);
  }
  return (c ^ 0xffffffff) >>> 0;
}
function chunk(type, data) {
  const t = Buffer.from(type),
    size = Buffer.alloc(4),
    check = Buffer.alloc(4);
  size.writeUInt32BE(data.length);
  check.writeUInt32BE(crc(Buffer.concat([t, data])));
  return Buffer.concat([size, t, data, check]);
}
export async function icons(dir) {
  for (const size of [16, 32, 48, 128]) {
    const raw = Buffer.alloc(size * (1 + size * 4));
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const colors = [0, 0, 0, 0];
        for (let sy = 0; sy < 4; sy++)
          for (let sx = 0; sx < 4; sx++) {
            const u = ((x + (sx + 0.5) / 4) * 64) / size,
              v = ((y + (sy + 0.5) / 4) * 64) / size;
            let col = [240, 242, 235, 255];
            const t = Math.max(0, Math.min(1, (u - 23) / 31));
            const half =
              u < 23
                ? 23 * Math.sqrt(Math.max(0, 1 - ((u - 23) / 14) ** 2))
                : u <= 54
                  ? 1.7 + 21.3 * (1 - t) ** 2.4 * (1 + 2.4 * t)
                  : 1.7 * Math.sqrt(Math.max(0, 1 - ((u - 54) / 2) ** 2));
            if (u >= 9 && u <= 56 && Math.abs(v - 32) <= half) {
              col =
                u < 25
                  ? [125, 159, 136, 255]
                  : u < 40
                    ? [87, 130, 109, 255]
                    : [48, 96, 77, 255];
              const seam = size <= 16 ? 1.7 : 1.1;
              if (
                Math.abs(u - 25) < seam ||
                Math.abs(u - 40) < seam ||
                (u < 25 &&
                  [20.5, 32, 43.5].some((y) => Math.abs(v - y) < seam)) ||
                (u >= 25 && u < 40 && Math.abs(v - 32) < seam)
              )
                col = [240, 242, 235, 255];
            }
            for (let c = 0; c < 4; c++) colors[c] += col[c] / 16;
          }
        const offset = y * (1 + size * 4) + 1 + x * 4;
        for (let c = 0; c < 4; c++) raw[offset + c] = colors[c];
      }
    }
    const head = Buffer.alloc(13);
    head.writeUInt32BE(size);
    head.writeUInt32BE(size, 4);
    head[8] = 8;
    head[9] = 6;
    await writeFile(
      `${dir}/icon${size}.png`,
      Buffer.concat([
        Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
        chunk("IHDR", head),
        chunk("IDAT", deflateSync(raw)),
        chunk("IEND", Buffer.alloc(0)),
      ]),
    );
  }
}
