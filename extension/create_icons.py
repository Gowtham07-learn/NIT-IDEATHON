"""Generate extension icons. Run from extension/ folder: python create_icons.py"""
import struct
import zlib
from pathlib import Path

def chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

def create_png(size):
    # PNG raw: each row = filter byte (0) + size * RGB
    row = b'\x00' + (b'\x1e\x29\x3b' * size)
    raw = row * size
    raw = zlib.compress(raw, 9)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', raw)
    png += chunk(b'IEND', b'')
    return png

icons_dir = Path(__file__).parent / 'icons'
icons_dir.mkdir(exist_ok=True)
for s in [16, 48, 128]:
    (icons_dir / f'icon{s}.png').write_bytes(create_png(s))
    print(f'Created icons/icon{s}.png')
