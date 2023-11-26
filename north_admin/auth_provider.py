from datetime import datetime as dt
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from north_admin.dto import JWTTokens, UserLoginSchema, UserReturnSchema
from north_admin.helpers import dt_to_int
from north_admin.types import ModelType
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/admin/api/token')


class AuthProvider:
    jwt_secret_key: str
    jwt_algorithm: str
    sqlalchemy_session_maker: async_sessionmaker[AsyncSession]

    def __init__(
        self,
        jwt_secret_key: str,
        sqlalchemy_session_maker: async_sessionmaker[AsyncSession],

    ):
        self.jwt_secret_key = jwt_secret_key
        self.jwt_algorithm = 'HS256'
        self.sqlalchemy_session_maker = sqlalchemy_session_maker

    async def login(
        self,
        session: AsyncSession,
        login: str,
        password: str,
    ) -> ModelType | None:
        raise NotImplementedError('Must by implemented in child class')

    async def get_user_by_id(
        self,
        session: AsyncSession,
        user_id: int | str,
    ) -> ModelType | None:
        raise NotImplementedError('Must by implemented in child class')

    async def to_user_scheme(
        self,
        user: ModelType,
    ) -> UserReturnSchema:
        raise NotImplementedError('Must by implemented in child class')

    async def login_endpoint(
        self,
        origin: UserLoginSchema,
    ) -> JWTTokens:
        async with self.sqlalchemy_session_maker() as session:
            user = await self.login(
                session=session,
                login=origin.login,
                password=origin.password,
            )
            if user is None:
                raise HTTPException(
                    status_code=401,
                    detail={
                        'Unauthorized': 'wrong login or password'
                    },
                )

            return self.create_jwt_tokens(user_id=user.id)

    async def token_endpoint(
        self,
        form_data: OAuth2PasswordRequestForm = Depends(),
    ) -> JWTTokens:
        async with self.sqlalchemy_session_maker() as session:
            user = await self.login(
                session=session,
                login=form_data.username,
                password=form_data.password,
            )
            if user is None:
                raise HTTPException(
                    status_code=401,
                    detail={
                        'Unauthorized': 'wrong login or password'
                    },
                )

            return self.create_jwt_tokens(user_id=user.id)

    async def get_auth_user_endpoint(
        self,
        token: Annotated[str, Depends(oauth2_scheme)],
    ) -> UserReturnSchema:
        user = await self.get_auth_user(token=token)
        return await self.to_user_scheme(user=user)

    async def get_auth_user(
        self,
        token: Annotated[str, Depends(oauth2_scheme)],
    ) -> ModelType:
        user_id = self.validate_access_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail='Wrong JWT Token')

        async with self.sqlalchemy_session_maker() as session:
            user = await self.get_user_by_id(
                session=session,
                user_id=user_id,
            )
            if not user:
                raise HTTPException(status_code=401, detail='Wrong JWT Token')

            return user

    def create_jwt_tokens(
        self,
        user_id: int | int,
    ) -> JWTTokens:
        access_token_data = {
            'user_id': user_id,
            'type': 'access',
            'expired_at': None,
        }

        access_token = jwt.encode(
            payload=access_token_data,
            key=self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
        )

        refresh_token_data = {
            'user_id': user_id,
            'access_token': access_token,
            'type': 'refresh',
        }

        refresh_token = jwt.encode(
            payload=refresh_token_data,
            key=self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
        )

        return JWTTokens(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def validate_access_token(
        self,
        access_token: str,
    ) -> str | None:
        """ Returning user_id """

        payload: dict

        try:
            payload = jwt.decode(
                jwt=access_token,
                key=self.jwt_secret_key,
                algorithms=self.jwt_algorithm,
            )
        except jwt.DecodeError:
            return None

        if (
            'user_id' not in payload.keys() or
            'type' not in payload.keys() or
            'expired_at' not in payload.keys()
        ):
            return None

        if payload['type'] != 'access':
            return None

        if payload['expired_at'] and payload['expired_at'] <= dt_to_int(dt.now()):
            return None

        return payload['user_id']
