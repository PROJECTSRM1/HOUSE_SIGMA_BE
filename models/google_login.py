from pydantic import BaseModel # pyright: ignore[reportMissingImports]

class GoogleLoginRequest(BaseModel):
    token: str
