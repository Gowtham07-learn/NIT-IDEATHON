"""Generate extension icons. Run: python create_icons.py"""
import base64
import struct
import zlib

def create_png(size):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    raw = b'\x08\x02'  # 8-bit, RGB
    raw += b''.join(b'\x00\x3b\x5f\x82' * size for _ in range(size))  # #1e293b fill
    raw = zlib.compress(raw, 9)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', raw)
    png += chunk(b'IEND', b'')
    return png

for s in [16, 48, 128]:
    open(f'icons/icon{s}.png', 'wb').write(create_png(s))
    print(f'Created icons/icon{s}.png')
