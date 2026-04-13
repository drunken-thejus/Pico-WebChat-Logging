import jwt
from jwt.exceptions import InvalidSignatureError,InvalidTokenError
from datetime import datetime,timedelta,timezone

SECRET_KEY="70e11c5ec22b62256520a0af4690f2201a585fb4bb699742308f1da15e5e9348"
LIFE_CYCLE=7
ALGORITHM="HS256"


def create_access_token(username:str):
    to_encode={
        "sub":username
    }
    expire=datetime.now(timezone.utc)+timedelta(days=LIFE_CYCLE)
    to_encode.update({"exp":expire})
    encode_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encode_jwt

def decode_token(token:str):
    try:
        return jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    except:
        None

