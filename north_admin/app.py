from fastapi import FastAPI

from sqlalchemy.pool import Pool, NullPool
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
    AsyncSession,
)


class NorthAdmin(FastAPI):
    sqlalchemy_engine: AsyncEngine
    sqlalchemy_session_maker: async_sessionmaker[AsyncSession]

    logo_url: str | None

    def __init__(
        self,
        sqlalchemy_db: str,
        sqlalchemy_host: str = '127.0.0.1',
        sqlalchemy_port: str = '5432',
        sqlalchemy_user: str = 'postgres',
        sqlalchemy_password: str = '',
        sqlalchemy_pool_class: Pool = NullPool,
        sqlalchemy_pool_size: int = 1,
        admin_title: str = 'Admin Panel',
        logo_url: str | None = None,
    ):
        self.sqlalchemy_engine = create_async_engine(
            (
                f'postgresql+asyncpg://{sqlalchemy_user}:'
                f'{sqlalchemy_password}@'
                f'{sqlalchemy_host}:'
                f'{sqlalchemy_port}/'
                f'{sqlalchemy_db}'
            ),
            echo=False,
            pool_size=sqlalchemy_pool_size,
            poolclass=sqlalchemy_pool_class,
        )

        self.sqlalchemy_session_maker = async_sessionmaker(
            bind=self.sqlalchemy_engine,
            expire_on_commit=False,
        )

        self.logo_url = logo_url

        super().__init__(
            title=admin_title,
            version='0.0.1',
        )
