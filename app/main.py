from fastapi import FastAPI
from app.routes import ops, client

app = FastAPI()

# ✅ Add this root route
@app.get("/")
def read_root():
    return {"message": "Welcome to the Secure File Sharing API!"}

app.include_router(ops.router, prefix="/ops", tags=["Ops User"])
app.include_router(client.router, prefix="/client", tags=["Client User"])
