from datetime import datetime as dt
from enum import Enum

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserType(str, Enum):
    USER = "user"
    ADMIN = "admin"
    ROOT = "root"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(nullable=False)
    fullname: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    user_type: Mapped[UserType] = mapped_column(ENUM(UserType, name="user_type"), default=UserType.USER)
    created_at: Mapped[dt] = mapped_column(default=dt.now, server_default=func.current_timestamp())


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    author: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_post_user_id",
        ),
    )
    title: Mapped[str]
    text: Mapped[str]
    is_approved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[dt] = mapped_column(default=dt.now, server_default=func.current_timestamp())
    approved_at: Mapped[dt | None]
