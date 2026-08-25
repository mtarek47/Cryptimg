import unittest
from stegstr.core.crypto import generate_key, encrypt_payload, decrypt_payload, CryptoError


class TestCrypto(unittest.TestCase):
    def test_encrypt_decrypt_roundtrip(self):
        key = generate_key()
        payload = b"Top Secret Stegstr Nostr Payload"
        ciphertext, nonce, auth_tag = encrypt_payload(payload, key)

        recovered = decrypt_payload(ciphertext, key, nonce, auth_tag)
        self.assertEqual(recovered, payload)

    def test_authentication_failure(self):
        key = generate_key()
        payload = b"Tamper Test"
        ciphertext, nonce, auth_tag = encrypt_payload(payload, key)

        # Tamper with ciphertext
        tampered_ct = bytearray(ciphertext)
        tampered_ct[0] ^= 0xFF

        with self.assertRaises(CryptoError):
            decrypt_payload(bytes(tampered_ct), key, nonce, auth_tag)


if __name__ == "__main__":
    unittest.main()
