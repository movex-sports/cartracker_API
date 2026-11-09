import unittest

from gt06 import (
    FrameBuffer,
    build_ack,
    crc16_x25,
    decode_imei,
    decode_location,
    parse_packet,
)


def make_packet(protocol: int, information: bytes, serial: bytes = b"\x00\x01") -> bytes:
    length = 1 + len(information) + 2 + 2
    body = bytes((length, protocol)) + information + serial
    return b"\x78\x78" + body + crc16_x25(body).to_bytes(2, "big") + b"\x0d\x0a"


class GT06Tests(unittest.TestCase):
    def test_fragmented_login_and_ack(self) -> None:
        raw = make_packet(0x01, bytes.fromhex("0357012345678901"), b"\x12\x34")
        buffer = FrameBuffer()
        self.assertEqual(buffer.feed(raw[:5]), [])
        frames = buffer.feed(raw[5:])
        self.assertEqual(frames, [raw])
        packet = parse_packet(frames[0])
        self.assertTrue(packet.valid_crc)
        self.assertEqual(decode_imei(packet.information), "357012345678901")
        ack = parse_packet(build_ack(packet))
        self.assertTrue(ack.valid_crc)
        self.assertEqual(ack.protocol, 0x01)
        self.assertEqual(ack.serial, b"\x12\x34")

    def test_multiple_packets_in_one_read(self) -> None:
        first = make_packet(0x13, b"\x42\x05\x04")
        second = make_packet(0x13, b"\x40\x04\x03", b"\x00\x02")
        self.assertEqual(FrameBuffer().feed(first + second), [first, second])

    def test_crc_failure_is_reported(self) -> None:
        raw = bytearray(make_packet(0x13, b"\x42\x05\x04"))
        raw[-4] ^= 0xFF
        self.assertFalse(parse_packet(bytes(raw)).valid_crc)

    def test_real_j16_location_packet(self) -> None:
        raw = bytes.fromhex(
            "78781f121a0a11150d3ac8028602410506e6810058ac"
            "0000000000000000000443fa0d0a"
        )
        packet = parse_packet(raw)
        location = decode_location(packet)
        self.assertTrue(packet.valid_crc)
        self.assertTrue(location["gps_valid"])
        self.assertTrue(location["realtime"])
        self.assertAlmostEqual(location["latitude"], -23.5204628, places=6)
        self.assertAlmostEqual(location["longitude"], -46.8546139, places=6)
        self.assertEqual(location["speed"], 0)
        self.assertEqual(location["course"], 172)


if __name__ == "__main__":
    unittest.main()
