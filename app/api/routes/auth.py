from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_auth_service
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=201,
)
def register(
    data: UserCreate,
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
):
    return auth_service.register_user(data)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
):
    token = auth_service.login_user(
        data.email,
        data.password,
    )

    return TokenResponse(
        access_token=token,
    )