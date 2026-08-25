import os
import unittest
from PIL import Image
import numpy as np
from stegstr.stego.engine import StegEngine


class TestFuzzing(unittest.TestCase):
    def setUp(self):
        self.engine = StegEngine()

    def test_random_noise_image(self):
        # Decode pure random noise image; must fail cleanly without throwing crash
        arr = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
        img = Image.fromarray(arr, mode="RGB")
        res = self.engine.decode(img)
        self.assertEqual(res["status"], "NONE")

    def test_blank_black_image(self):
        arr = np.zeros((200, 200, 3), dtype=np.uint8)
        img = Image.fromarray(arr, mode="RGB")
        res = self.engine.decode(img)
        self.assertEqual(res["status"], "NONE")


if __name__ == "__main__":
    unittest.main()
