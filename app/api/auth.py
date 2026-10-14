from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models import User
from app.schemas.auth import AuthenticatedUser, LoginRequest, LoginResponse
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
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> LoginResponse:
    request.session.clear()
    user = authenticate_user(session, credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
        )
    request.session["user_id"] = user.id
    return LoginResponse(id=user.id, username=user.username)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={204: {"description": "Sesión cerrada."}},
)
def logout(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=AuthenticatedUser,
    responses={401: {"description": "Sesión ausente, inválida o usuario inactivo."}},
)
def read_current_user(
    user: Annotated[User, Depends(get_current_user)],
) -> AuthenticatedUser:
    return AuthenticatedUser(id=user.id, username=user.username)
