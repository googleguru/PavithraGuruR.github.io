"""
TinyTapeout integration — generate and validate info.yaml ROM metadata,
mirror the tt-chip-rom encoding scheme used by tt-support-tools.
"""
from __future__ import annotations
import struct
import yaml
from pathlib import Path

INFO_YAML = Path(__file__).parent.parent / "info.yaml"

# 7-segment encoding table (0–9, A–F + space)
_SEG7 = {
    " ": 0x00, "0": 0x3F, "1": 0x06, "2": 0x5B, "3": 0x4F,
    "4": 0x66, "5": 0x6D, "6": 0x7D, "7": 0x07, "8": 0x7F,
    "9": 0x6F, "A": 0x77, "B": 0x7C, "C": 0x39, "D": 0x5E,
    "E": 0x79, "F": 0x71, "-": 0x40, "_": 0x08,
}
_MAGIC = b"\xDE\xAD\xBE\xEF"


def load_info() -> dict:
    with INFO_YAML.open() as f:
        return yaml.safe_load(f)


def encode_7seg(text: str, length: int) -> bytes:
    """Encode text as 7-segment bytes, padded/truncated to length."""
    result = bytearray(length)
    for i, ch in enumerate(text.upper()[:length]):
        result[i] = _SEG7.get(ch, 0x00)
    return bytes(result)


def crc32(data: bytes) -> bytes:
    import binascii
    crc = binascii.crc32(data) & 0xFFFFFFFF
    return struct.pack("<I", crc)


def build_rom(info: dict | None = None) -> bytes:
    """Build 256-byte ROM image matching tt-chip-rom layout."""
    if info is None:
        info = load_info()

    rom = bytearray(256)
    shuttle = info["rom"]["shuttle_name"]
    descriptor = info["rom"]["chip_descriptor"]

    # Addresses 0–7: shuttle name (7-seg encoded, 8 bytes)
    rom[0:8] = encode_7seg(shuttle, 8)
    # Addresses 8–31: git commit placeholder (24 bytes, all zeros = not set)
    # Addresses 32–127: chip descriptor (ASCII, 96 bytes)
    desc_bytes = descriptor.encode("ascii", errors="replace")[:96]
    rom[32 : 32 + len(desc_bytes)] = desc_bytes
    # Addresses 248–251: magic value
    rom[248:252] = _MAGIC
    # Addresses 252–255: CRC32 over bytes 0–251
    rom[252:256] = crc32(bytes(rom[:252]))

    return bytes(rom)


def write_rom(out_path: Path | None = None) -> Path:
    if out_path is None:
        out_path = Path(__file__).parent.parent / "tt_chip_rom.bin"
    data = build_rom()
    out_path.write_bytes(data)
    print(f"[TinyTapeout] ROM image written → {out_path}  ({len(data)} bytes)")
    return out_path


def validate_info(info: dict | None = None) -> list[str]:
    """Return list of validation errors (empty = OK)."""
    if info is None:
        info = load_info()
    errors: list[str] = []
    proj = info.get("project", {})
    for key in ("title", "author", "description", "language", "tiles"):
        if not proj.get(key):
            errors.append(f"project.{key} is missing or empty")
    if proj.get("tiles") not in ("1x1", "1x2", "2x2", "4x2"):
        errors.append(f"project.tiles value '{proj.get('tiles')}' is not a standard TT tile size")
    return errors
