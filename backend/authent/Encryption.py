
from cryptography.fernet import Fernet

import os

# Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRATION = 60 * 24 * 7

# Encode the key
fernet = Fernet(ENCRYPTION_KEY.encode())

# Encrypt google token
def encrypt_token(token: str) -> bytes:
    return fernet.encrypt(token.encode())

# Decrypt google token
def decrypt_token(encrypted_token: bytes) -> str:
    return fernet.decrypt(encrypted_token).decode()

