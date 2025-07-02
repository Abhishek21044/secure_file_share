from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    is_ops: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class FileResponse(BaseModel):
    filename: str
    path: str

class DownloadResponse(BaseModel):
    download_link: str
    message: str
