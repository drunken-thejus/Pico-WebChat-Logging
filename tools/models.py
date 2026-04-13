from pydantic import BaseModel

class  DataPipe(BaseModel):
    type:str
    data:dict

class DataError(BaseModel):
    log:str

class DataMessagePublic(BaseModel):
    type:str="public"
    message:str
    sender:str

class DataMessagePrivate(DataMessagePublic):
    type:str="private"
    receiver:str

class ActiveUserList(BaseModel):
    users:list

class ActiveUserCount(BaseModel):
    count:int