import unittest
from stegstr.nostr.keys import NostrKeyPair
from stegstr.nostr.events import NostrEvent


class TestNostr(unittest.TestCase):
    def test_keypair_generation_and_bech32(self):
        kp = NostrKeyPair.generate_anonymous()
        self.assertTrue(kp.nsec.startswith("nsec1"))
        self.assertTrue(kp.npub.startswith("npub1"))

        kp_restored = NostrKeyPair.from_nsec(kp.nsec)
        self.assertEqual(kp_restored.public_key_hex, kp.public_key_hex)

    def test_event_signing_and_verification(self):
        kp = NostrKeyPair.generate_anonymous()
        evt = NostrEvent.create_text_note(kp, "Hello Nostr Verification!")
        self.assertTrue(evt.verify())

        # Tamper with event content
        evt.content = "Tampered Content"
        self.assertFalse(evt.verify())


if __name__ == "__main__":
    unittest.main()
