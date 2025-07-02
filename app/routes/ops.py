from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app import models, database, auth
from fastapi.security import OAuth2PasswordRequestForm
import shutil

router = APIRouter()

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not user.is_ops:
        raise HTTPException(status_code=403, detail="Not authorized")
    token = auth.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/upload")
def upload_file(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    allowed_extensions = ['pptx', 'docx', 'xlsx']
    extension = file.filename.split(".")[-1]
    if extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_file = models.File(filename=file.filename, path=file_path, uploader_id=1)  # Assume uploader_id = 1 for now
    db.add(new_file)
    db.commit()

    return {"message": "File uploaded successfully"}
