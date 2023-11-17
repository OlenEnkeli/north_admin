from typing import Literal

from sqlalchemy.orm import DeclarativeBase
from fastapi import FastAPI

from sqlalchemy.pool import Pool, NullPool
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
    AsyncSession,
)
from sqlalchemy.orm.attributes import InstrumentedAttribute


class NorthAdmin(FastAPI):
    sqlalchemy_engine: AsyncEngine
    sqlalchemy_session_maker: async_sessionmaker[AsyncSession]

    logo_url: str | None

    def __init__(
        self,
        sqlalchemy_db: str,
        sqlalchemy_server: str = '127.0.0.1:5432',
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
                f'{sqlalchemy_user}/'
                f'{sqlalchemy_server}:'
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

    def add_admin_route(
        self,
        model: DeclarativeBase,
        enabled_methods: list[
            Literal[
                'get_list',
                'get_one',
                'create',
                'update',
                'soft_delete',
                'delete',
            ]
        ] | None = None,
        list_fields: list[InstrumentedAttribute] | None = None,
        get_fields: list[InstrumentedAttribute] | None = None,
        create_fields: list[InstrumentedAttribute] | None = None,
        update_fields: list[InstrumentedAttribute] | None = None,
        soft_delete_field: InstrumentedAttribute | None = None,
        sortable_fields: list[InstrumentedAttribute] | None = None,
        filters: dict[
          str,
          tuple[
              InstrumentedAttribute,
              Literal['checkbox', 'gt', 'lt'],
          ],
        ] | None = None,
    ) -> None:
        if not enabled_methods:
            enabled_methods = ['get_list', 'get_one', 'create', 'update', 'soft_delete', 'delete']
