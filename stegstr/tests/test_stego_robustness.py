import unittest
from PIL import Image
import numpy as np
from stegstr.stego.engine import StegEngine


class TestStegoRobustness(unittest.TestCase):
    def setUp(self):
        self.engine = StegEngine()
        # Create synthetic test carrier image (300x300 textured RGB image)
        arr = np.random.randint(0, 256, (300, 300, 3), dtype=np.uint8)
        self.cover_img = Image.fromarray(arr, mode="RGB")

    def test_robust_dct_encode_decode(self):
        payload = b"Stegstr DCT QIM Robustness Unit Test Payload"
        enc = self.engine.encode(self.cover_img, payload, mode="robust", robustness="balanced")
        
        self.assertGreater(enc["psnr_db"], 30.0)
        self.assertGreater(enc["ssim"], 0.90)

        dec = self.engine.decode(enc["stego_image"])
        self.assertEqual(dec["status"], "FOUND")
        self.assertEqual(dec["payload"], payload)

    def test_legacy_png_encode_decode(self):
        payload = b"Legacy PNG Payload Test"
        enc = self.engine.encode(self.cover_img, payload, mode="legacy", robustness="fast")
        dec = self.engine.decode(enc["stego_image"])
        self.assertEqual(dec["status"], "FOUND")
        self.assertEqual(dec["payload"], payload)


if __name__ == "__main__":
    unittest.main()
