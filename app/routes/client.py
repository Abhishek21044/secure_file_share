from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, auth, database
from fastapi.security import OAuth2PasswordRequestForm
import base64, os
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/client/login")

@router.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password, is_ops=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Signup successful", "verify-url": f"/client/verify/{new_user.id}"}

@router.get("/verify/{user_id}")
def verify_email(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    db.commit()
    return {"message": "Email verified successfully"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    token = auth.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/files")
def list_files(db: Session = Depends(database.get_db)):
    files = db.query(models.File).all()
    return [{"id": f.id, "filename": f.filename} for f in files]

@router.get("/download-file/{file_id}")
def get_download_link(file_id: int, db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    user = db.query(models.User).filter(models.User.email == payload.get("sub")).first()
    if user.is_ops:
        raise HTTPException(status_code=403, detail="Only client can download files")

    file = db.query(models.File).filter(models.File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    encrypted_path = base64.urlsafe_b64encode(file.path.encode()).decode()
    return {"download_link": f"/client/download/{encrypted_path}", "message": "success"}

@router.get("/download/{encrypted_path}")
def download_file(encrypted_path: str):
    try:
        decoded_path = base64.urlsafe_b64decode(encrypted_path.encode()).decode()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid download link")
    if not os.path.exists(decoded_path):
        raise HTTPException(status_code=404, detail="File not found")

    return {"message": "You would download this file here", "file_path": decoded_path}
