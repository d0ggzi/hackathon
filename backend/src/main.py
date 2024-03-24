import fastapi
import fastapi.security as _security
from fastapi import Security
import json
from fastapi.responses import JSONResponse

import sqlalchemy.orm as _orm
import services as _services, schemas as _schemas
from fastapi.middleware.cors import CORSMiddleware

app = fastapi.FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


allowed_users = {"admin@admin.com"}


def authenticate_user(user=Security(_services.get_current_user)):
    if user.email not in allowed_users:
        raise fastapi.HTTPException(status_code=401, detail="Недостаточно прав")
    return user


@app.post("/api/users")
async def create_user(
        user: _schemas.UserCreate
):
    db_user = await _services.get_user_by_email(user.email)
    if db_user:
        raise fastapi.HTTPException(status_code=400, detail="Email already in use")

    user = await _services.create_user(user)

    return user


@app.post("/api/token")
async def generate_token(
        form_data: _security.OAuth2PasswordRequestForm = fastapi.Depends(),
):
    user: _schemas.User = await _services.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise fastapi.HTTPException(status_code=401, detail="Invalid Credentials")

    return await _services.create_token(user)


@app.get("/api/users/me", response_model=_schemas.User)
async def get_user(user=fastapi.Depends(_services.get_current_user)):
    return user


@app.get("/api/users/admin", response_model=_schemas.User)
async def get_user(user=fastapi.Depends(authenticate_user)):
    return user


@app.get("/api/data/roadmap")
async def get_roadmap(project_name: str, user=fastapi.Depends(_services.get_current_user)):
    try:
        with open(f'../resources/{project_name}.json') as f:
            data = json.load(f)
            return JSONResponse(data)
    except FileNotFoundError:
        raise fastapi.HTTPException(status_code=404, detail="Project not found")


@app.get("/api/data/tasks")
async def get_tasks(user=fastapi.Depends(_services.get_current_user)):
    return await _services.get_team_tasks(user)


@app.get("/api/data/teams")
async def get_teams():
    return await _services.get_teams()


@app.get("/api/parse")
async def parse():
    from excelParser import parseExcelTasks
    parseExcelTasks("../resources/Sample1.xlsx")