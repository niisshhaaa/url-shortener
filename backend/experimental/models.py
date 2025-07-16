class UserCreateModel(BaseModel):
    username:Union[str,None]=None
    email:str
    password:str

class LoginInput(BaseModel):
    email:str
    password:str

class Token(BaseModel):
    access_token:str
    refresh_token:str
    token_type:str="bearer"