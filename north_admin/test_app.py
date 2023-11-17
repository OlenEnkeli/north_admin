from datetime import datetime as dt

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


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
    telegram: Mapped[str] = mapped_column(nullable=True)

    is_active: Mapped[bool] = mapped_column(default=False)

    verification_code: Mapped[str] = mapped_column(nullable=True)
    password_reset_code: Mapped[str] = mapped_column(nullable=True)