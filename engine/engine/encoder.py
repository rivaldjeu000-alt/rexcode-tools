import os
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

def seed_from_content(data: bytes) -> int:
    s, cum = 1, 0
    for b in data:
        s = (s + (b & 0xFF)) & 0xFFFFFFFF
        cum = (cum + s) & 0xFFFFFFFF
    seed = ((s | (cum << 16)) >> 16) ^ (0xFFFF & s)
    seed |= (os.urandom(1)[0] + 1) << 16
    return seed & 0xFFFFFFFF

def lz4_encode(data: bytes) -> bytes:
    compressed = lz4.block.compress(data, store_size=False)
    header = struct.pack('<4sI', b'\x04\x22\x4D\x18', len(data))
    return header + compressed

def xor_encode(data: bytes, seed_override=None) -> bytes:
    size = len(data)
    hl = ((235176 ^ size) + ((8 + size) ^ 810733)) & 0xFFFFFFFF
    seed = seed_override if seed_override else seed_from_content(data)
    header = bytes([121,
        (hl >> 0) & 0xFF, (hl >> 8) & 0xFF, (hl >> 16) & 0xFF,
        (seed >> 0) & 0xFF, (seed >> 8) & 0xFF,
        (seed >> 16) & 0xFF, (seed >> 24) & 0xFF])
    table = get_hash_table(hl, (seed + 4) & 0xFFFFFFFF)
    payload = bytearray(data)
    prev = 0
    j = 0
    for i in range(size):
        curr = payload[i]
        payload[i] = (table[j] ^ curr) & 0xFF
        payload[i] = (payload[i] + prev) & 0xFF
        prev = curr
        j = (j + 1) % 727
    return header + payload

def encode_full(xml_bytes: bytes, use_lz4: bool = True) -> bytes:
    payload = lz4_encode(xml_bytes) if use_lz4 else xml_bytes
    return xor_encode(payload)
