from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ErreurMetier(Exception):
    """Classe de base : chaque sous-classe porte son code HTTP."""

    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class IntrouvableError(ErreurMetier):
    status_code = 404  # ressource inconnue


class ConflitError(ErreurMetier):
    status_code = 409  # doublon, transition interdite, solde dépassé...


class ValidationMetierError(ErreurMetier):
    status_code = 422  # valeur interdite par une règle de gestion


class InterditError(ErreurMetier):
    status_code = 403  # ex. le tailleur ne peut pas annuler (RG14)


class NonAuthentifieError(ErreurMetier):
    status_code = 401  # identifiants incorrects, compte désactivé


def enregistrer_handlers(app: FastAPI) -> None:
    """Un seul handler pour toutes les erreurs métier : {"detail": "..."}."""

    @app.exception_handler(ErreurMetier)
    async def _handler(request: Request, exc: ErreurMetier):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
            headers=headers,
        )