from pwdlib  import PasswordHash

passwordhash=PasswordHash.recommended()

def hash_this_passowrd(password:str):
    return passwordhash.hash(password)

def verify_this_passowrd(password:str,hashed_password:str):
    return passwordhash.verify(password,hashed_password)