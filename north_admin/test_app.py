from datetime import datetime as dt

from fastapi import FastAPI
from sqlalchemy import create_engine, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from north_admin import NorthAdmin, setup_admin


class Base(AsyncAttrs, DeclarativeBase):
    created_at: Mapped[dt] = mapped_column(
        nullable=False,
        default=dt.now,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[dt] = mapped_column(
        nullable=True,
        default=None,
        onupdate=func.current_timestamp(),
    )


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(nullable=False)
    fullname: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False)


engine = create_engine(
    'postgresql+psycopg://postgres:@127.0.0.1:5432/north_admin_test_app',
)
session_maker = sessionmaker(bind=engine)


app = FastAPI()
admin_app = NorthAdmin(
    sqlalchemy_uri='postgresql+asyncpg://postgres:@127.0.0.1:5432/north_admin_test_app',
)

user_get_columns = [User.id, User.email, User.fullname, User.is_active, User.created_at, User.updated_at]

admin_app.add_admin_routes(
    model=User,
    model_title='Users',
    pkey_column=User.id,
    soft_delete_column=User.is_active,
    get_columns=user_get_columns,
    list_columns=user_get_columns,
    update_columns=[User.email, User.fullname, User.is_active],
    create_columns=[User.email, User.fullname, User.is_active, User.password],
)
setup_admin(
    app=app,
    admin_app=admin_app,
)

Base.metadata.create_all(bind=engine)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app=app)
