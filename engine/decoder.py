import struct
import lz4.block

def mmh2(data: bytes, seed: int) -> int:
    h = (seed ^ len(data)) & 0xFFFFFFFF
    i, length = 0, len(data)
    while length >= 4:
        k = struct.unpack_from('<I', data, i)[0]
        k = (k * 0x5bd1e995) & 0xFFFFFFFF
        k ^= (k >> 24)
        k = (k * 0x5bd1e995) & 0xFFFFFFFF
        h = (h * 0x5bd1e995) & 0xFFFFFFFF
        h ^= k
        i += 4
        length -= 4
    if length >= 3: h ^= (data[i+2] & 0xFF) << 16
    if length >= 2: h ^= (data[i+1] & 0xFF) << 8
    if length >= 1:
        h = ((h ^ (data[i] & 0xFF)) * 0x5bd1e995) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5bd1e995) & 0xFFFFFFFF
    h ^= h >> 15
    return h & 0xFFFFFFFF

def get_hash_table(length: int, seed: int) -> bytes:
    table = bytearray(727)
    h = seed & 0xFFFFFFFF
    i = 0
    while i < 727:
        v = bytes([(h>>0)&0xFF, (h>>8)&0xFF, (h>>16)&0xFF, (h>>24)&0xFF])
        h = mmh2(v, length & 0xFFFFFFFF)
        hb = bytes([(h>>0)&0xFF, (h>>8)&0xFF, (h>>16)&0xFF, (h>>24)&0xFF])
        for j in range(4):
            if i + j < 727:
                table[i + j] = hb[j]
        i += 4
    return bytes(table)

def xor_decode(data: bytes) -> bytes:
    hl = data[1] | (data[2] << 8) | (data[3] << 16)
    hs = struct.unpack_from('<I', data, 4)[0]
    src_size = len(data)
    table = get_hash_table(hl & 0xFFFFFFFF, (hs + 4) & 0xFFFFFFFF)
    sf = ((hl - (src_size ^ 810733)) & 0xFFFFFFFF) ^ 235176
    actual = min(sf, src_size - 8)
    out = bytearray(data[8:8+actual])
    j = 0
    for i in range(actual):
        if i > 0:
            out[i] = (out[i] - out[i-1]) & 0xFF
        out[i] ^= table[j]
        j = (j + 1) % 727
    return bytes(out)

def is_lz4(data: bytes) -> bool:
    return len(data) >= 8 and data[:4] == b'\x04\x22\x4D\x18'

def lz4_decode(data: bytes) -> bytes:
    unc = struct.unpack_from('<I', data, 4)[0]
    return lz4.block.decompress(data[8:], uncompressed_size=unc)

def trim_xml(data: bytes) -> bytes:
    marker = b"</root>"
    pos = -1
    for i in range(len(data)-1, -1, -1):
        if i + len(marker) <= len(data) and data[i:i+len(marker)] == marker:
            pos = i
            break
    if pos != -1:
        end = pos + len(marker)
        while end < len(data) and data[end] in (10, 13, 9, 32):
            end += 1
        return data[:end]
    end = len(data)
    while end > 0 and data[end-1] == 0:
        end -= 1
    return data[:end]

def decode_full(data: bytes) -> bytes:
    payload = xor_decode(data)
    if is_lz4(payload):
        payload = lz4_decode(payload)
    return trim_xml(payload)
