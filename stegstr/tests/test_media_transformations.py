import unittest
import io
from PIL import Image
import numpy as np

from stegstr.stego.engine import StegEngine
from benchmarks.benchmark_suite import apply_transformation, calculate_ber


class TestMediaTransformations(unittest.TestCase):
    def setUp(self):
        self.engine = StegEngine()
        # Synthetic textured image (400x400)
        arr = np.random.randint(40, 210, (400, 400, 3), dtype=np.uint8)
        self.cover_img = Image.fromarray(arr, mode="RGB")
        self.payload = b"Transformation Resilience Verification Payload 12345"

    def test_jpeg_q95_transformation(self):
        enc = self.engine.encode(self.cover_img, self.payload, mode="robust", robustness="balanced")
        transformed = apply_transformation(enc["stego_image"], "jpeg_q95")
        dec = self.engine.decode(transformed)
        self.assertEqual(dec["status"], "FOUND")
        self.assertIn(self.payload, dec["payload"])

    def test_jpeg_q85_transformation(self):
        enc = self.engine.encode(self.cover_img, self.payload, mode="robust", robustness="balanced")
        transformed = apply_transformation(enc["stego_image"], "jpeg_q85")
        dec = self.engine.decode(transformed)
        self.assertEqual(dec["status"], "FOUND")
        self.assertIn(self.payload, dec["payload"])

    def test_metadata_stripping(self):
        enc = self.engine.encode(self.cover_img, self.payload, mode="robust", robustness="balanced")
        transformed = apply_transformation(enc["stego_image"], "metadata_stripped")
        dec = self.engine.decode(transformed)
        self.assertEqual(dec["status"], "FOUND")
        self.assertIn(self.payload, dec["payload"])

    def test_repeated_compression(self):
        enc = self.engine.encode(self.cover_img, self.payload, mode="robust", robustness="robust")
        transformed = apply_transformation(enc["stego_image"], "repeated_compression_3x")
        dec = self.engine.decode(transformed)
        self.assertEqual(dec["status"], "FOUND")
        self.assertIn(self.payload, dec["payload"])


if __name__ == "__main__":
    unittest.main()
