
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import requests

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login_for_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Proxy login: call Django core to obtain a JWT access token.
    """
    core_url = "http://127.0.0.1:8000/api/token/"
    data = {"username": form_data.username, "password": form_data.password}
    response = requests.post(core_url, json=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token_data = response.json()
    return {"access_token": token_data.get("access"), "token_type": "bearer"}

from .report import router as report_router
app.include_router(report_router)
