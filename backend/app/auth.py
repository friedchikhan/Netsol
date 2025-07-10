from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class LoginForm(BaseModel):
    username: str
    password: str
    
async def login_handler(form: LoginForm):
    return {"access_token": form.username, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"username": token}