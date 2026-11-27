"""Offline validation only. Never creates or executes payments."""
import re

def valid_pix(code):
    if not isinstance(code, str) or not 20 <= len(code) <= 1024:
        return False
    try:
        raw = code.encode("ascii")
    except UnicodeEncodeError:
        return False
    if not raw.startswith(b"000201") or raw[-8:-4] != b"6304" or not re.fullmatch(rb"[0-9A-Fa-f]{4}", raw[-4:]):
        return False
    crc = 0xffff
    for byte in raw[:-4]:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xffff if crc & 0x8000 else (crc << 1) & 0xffff
    if crc != int(raw[-4:], 16):
        return False
    fields = {}
    i = 0
    while i < len(raw):
        header = raw[i:i+4]
        if len(header) != 4 or not header.isdigit():
            return False
        tag, length = header[:2], int(header[2:])
        i += 4
        if not length or i + length > len(raw) or tag in fields:
            return False
        fields[tag] = raw[i:i+length]
        i += length
    return (fields.get(b"00") == b"01" and fields.get(b"53") == b"986"
            and fields.get(b"58") == b"BR" and fields.get(b"63") == raw[-4:]
            and any(b"br.gov.bcb.pix" in value.lower() for tag,value in fields.items()
                    if 26 <= int(tag) <= 51))
