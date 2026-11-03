from pydantic import BaseModel


class Token(BaseModel):
    """Réponse du login (route 1)."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # durée de validité en secondes