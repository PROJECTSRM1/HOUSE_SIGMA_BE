import os
from fastapi import FastAPI  # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # pyright: ignore[reportMissingImports]
from fastapi.staticfiles import StaticFiles  # pyright: ignore[reportMissingImports]

# ---------------------------
# ROUTER IMPORTS
# ---------------------------
from routes.email_auth import router as email_router
from routes.google_auth import router as google_router
from routes.chat_router import router as chatbot_router


# ---------------------------
# APP INIT
# ---------------------------
app = FastAPI(title="Python FastAPI MVC Backend")

# ---------------------------
# STATIC FILES
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

# ---------------------------
# CORS (FULLY UPDATED FOR GOOGLE SIGN-IN)
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",

        # Google Identity
        "https://accounts.google.com",
        "https://www.googleapis.com",
        "https://apis.google.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# ROUTERS
# ---------------------------
app.include_router(email_router)
app.include_router(google_router)
app.include_router(chatbot_router)

# ---------------------------
# ROOT ENDPOINT
# ---------------------------
@app.get("/")
def home():
    return {"message": "FastAPI Backend Running"}

# ---------------------------
# DEV SERVER
# ---------------------------
if __name__ == "__main__":
    import uvicorn  # pyright: ignore[reportMissingImports]
    uvicorn.run(app, host="0.0.0.0", port=8000)
