import unittest
from stegstr.core.binary_protocol import StegstrPacket, BinaryProtocolError


class TestBinaryProtocol(unittest.TestCase):
    def test_packet_pack_unpack(self):
        payload = b'{"kind": 1, "content": "Binary Protocol Test Note"}'
        pkt = StegstrPacket(mode=0x02, flags=0x01, payload=payload)
        packed = pkt.pack()

        unpacked = StegstrPacket.unpack(packed)
        self.assertEqual(unpacked.payload, payload)
        self.assertEqual(unpacked.mode, 0x02)

    def test_crc_corruption_detection(self):
        payload = b"Payload for CRC corruption test"
        pkt = StegstrPacket(payload=payload)
        packed = bytearray(pkt.pack())

        # Corrupt single byte
        packed[10] ^= 0xFF

        with self.assertRaises(BinaryProtocolError):
            StegstrPacket.unpack(bytes(packed))


if __name__ == "__main__":
    unittest.main()
