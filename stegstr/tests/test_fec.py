import unittest
from stegstr.core.fec import ReedSolomonFEC, interleave_bytes, deinterleave_bytes


class TestFEC(unittest.TestCase):
    def test_rs_fec_encode_decode(self):
        fec = ReedSolomonFEC(robustness_level="balanced")
        data = b"Hello Stegstr Forward Error Correction Test Data"
        encoded = fec.encode(data)
        self.assertGreater(len(encoded), len(data))

        # Corrupt bytes in encoded stream
        corrupted = bytearray(encoded)
        corrupted[2] ^= 0xFF
        corrupted[10] ^= 0xAA

        recovered = fec.decode(bytes(corrupted), target_length=len(data))
        self.assertEqual(recovered, data)

    def test_interleaving_roundtrip(self):
        data = b"0123456789ABCDEF0123456789ABCDEF"
        interleaved = interleave_bytes(data, stride=8)
        deinterleaved = deinterleave_bytes(interleaved, stride=8, original_len=len(data))
        self.assertEqual(deinterleaved, data)


if __name__ == "__main__":
    unittest.main()
