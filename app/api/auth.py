from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth import authenticate_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"description": "Credenciales inválidas o cuenta inactiva."},
        422: {"description": "Solicitud inválida."},
    },
)
def login(
    credentials: LoginRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> LoginResponse:
    user = authenticate_user(session, credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
        )
    return LoginResponse(id=user.id, username=user.username)
