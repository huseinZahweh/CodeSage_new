from fastapi import FastAPI
from routers import auth, problems, profile
from errors import APIError, handle_api_error

app = FastAPI()
app.include_router(auth.router)
app.include_router(problems.router)
app.include_router(profile.router)
app.add_exception_handler(APIError, handle_api_error)