import os
import json
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes

class WalletManager:
    def __init__(self, wallet_file="user_wallet.json"):
        self.wallet_file = wallet_file
        self.key = None

    def create_new_key(self):
        self.key = ec.generate_private_key(ec.SECP256R1())
        self._save_key_to_file()

    def load_key(self) -> bool:
        if not os.path.isfile(self.wallet_file):
            return False
        with open(self.wallet_file, "r") as f:
            data = json.load(f)
            private_key_bytes = bytes.fromhex(data["private_key_hex"])
            self.key = serialization.load_der_private_key(private_key_bytes, password=None)
        return True

    def sign_data(self, data: bytes) -> bytes:
        if not self.key:
            raise ValueError("No private key loaded.")
        # Provide the hash algorithm:
        return self.key.sign(data, ec.ECDSA(hashes.SHA256()))

    def get_public_key_bytes(self) -> bytes:
        if not self.key:
            raise ValueError("Key not loaded or created yet.")
        pub = self.key.public_key()
        return pub.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def _save_key_to_file(self):
        private_bytes = self.key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        data = {"private_key_hex": private_bytes.hex()}
        with open(self.wallet_file, "w") as f:
            json.dump(data, f)
