"""Small, dependency-free GT06 framing and decoding helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


SHORT_HEADER = b"\x78\x78"
LONG_HEADER = b"\x79\x79"
STOP = b"\x0d\x0a"


def crc16_x25(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc ^ 0xFFFF


@dataclass(frozen=True)
class Packet:
    raw: bytes
    protocol: int
    information: bytes
    serial: bytes
    valid_crc: bool
    long_format: bool = False


class FrameBuffer:
    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[bytes]:
        self._buffer.extend(data)
        frames: list[bytes] = []
        while True:
            short = self._buffer.find(SHORT_HEADER)
            long = self._buffer.find(LONG_HEADER)
            starts = [position for position in (short, long) if position >= 0]
            if not starts:
                self._buffer[:] = self._buffer[-1:] if self._buffer[-1:] == b"\x78" else b""
                break
            start = min(starts)
            if start:
                del self._buffer[:start]
            is_long = self._buffer.startswith(LONG_HEADER)
            length_size = 2 if is_long else 1
            prefix_size = 2 + length_size
            if len(self._buffer) < prefix_size:
                break
            length = int.from_bytes(self._buffer[2:prefix_size], "big")
            total = prefix_size + length + len(STOP)
            if length < 5:
                del self._buffer[:2]
                continue
            if len(self._buffer) < total:
                break
            candidate = bytes(self._buffer[:total])
            del self._buffer[:total]
            if candidate.endswith(STOP):
                frames.append(candidate)
        return frames


def parse_packet(frame: bytes) -> Packet:
    long_format = frame.startswith(LONG_HEADER)
    if not (long_format or frame.startswith(SHORT_HEADER)) or not frame.endswith(STOP):
        raise ValueError("invalid GT06 frame markers")
    length_size = 2 if long_format else 1
    prefix_size = 2 + length_size
    declared = int.from_bytes(frame[2:prefix_size], "big")
    if len(frame) != prefix_size + declared + 2:
        raise ValueError("invalid GT06 frame length")
    protocol = frame[prefix_size]
    serial = frame[-6:-4]
    information = frame[prefix_size + 1 : -6]
    expected_crc = int.from_bytes(frame[-4:-2], "big")
    calculated_crc = crc16_x25(frame[2:-4])
    return Packet(frame, protocol, information, serial, expected_crc == calculated_crc, long_format)


def build_ack(packet: Packet) -> bytes:
    if packet.long_format:
        content = bytes((packet.protocol,)) + packet.serial
        length = (len(content) + 2).to_bytes(2, "big")
        crc = crc16_x25(length + content).to_bytes(2, "big")
        return LONG_HEADER + length + content + crc + STOP
    content = bytes((5, packet.protocol)) + packet.serial
    crc = crc16_x25(content).to_bytes(2, "big")
    return SHORT_HEADER + content + crc + STOP


def decode_imei(information: bytes) -> str:
    if len(information) < 8:
        raise ValueError("login packet has no complete IMEI")
    digits = information[:8].hex()
    return digits[1:] if digits.startswith("0") else digits


def decode_location(packet: Packet) -> dict[str, object]:
    info = packet.information
    if len(info) < 18:
        raise ValueError("location packet is too short")
    year, month, day, hour, minute, second = info[:6]
    timestamp = datetime(2000 + year, month, day, hour, minute, second, tzinfo=timezone.utc)
    latitude = int.from_bytes(info[7:11], "big") / 1_800_000
    longitude = int.from_bytes(info[11:15], "big") / 1_800_000
    course_status = int.from_bytes(info[16:18], "big")
    # In the GT06 course/status word, bit 12 marks south and bit 13
    # distinguishes east from west. The lower ten bits contain the course.
    if course_status & 0x1000:
        latitude = -latitude
    if not course_status & 0x2000:
        longitude = -longitude
    return {
        "timestamp": timestamp.isoformat(),
        "satellites": info[6] & 0x0F,
        "latitude": latitude,
        "longitude": longitude,
        "speed": info[15],
        "course": course_status & 0x03FF,
        "gps_valid": bool(course_status & 0x4000),
        "realtime": not bool(course_status & 0x8000),
    }


def decode_heartbeat(packet: Packet) -> dict[str, object]:
    if len(packet.information) < 3:
        raise ValueError("heartbeat packet is too short")
    terminal, battery_level, gsm_signal = packet.information[:3]
    return {
        "ignition": bool(terminal & 0x02),
        "charging": bool(terminal & 0x04),
        "gps_tracking": bool(terminal & 0x40),
        "battery_level": battery_level,
        "gsm_signal": gsm_signal,
    }
