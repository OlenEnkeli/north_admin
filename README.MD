# NorthAdmin

Easy-to-setup PWA Admin Panel solution based on FastAPI, async SQLAlchemy and pre-render Swelte UI.

___

[PyPI](https://pypi.org/project/north_admin/) | [GitHub](https://github.com/OlenEnkeli/north_admin) | [Example App](https://github.com/OlenEnkeli/north_admin_testapp) | [Frontend](https://github.com/OlenEnkeli/north_admin_frontend)

___

**This is beta-version and frontend part (UI) currenly is in development.**

**Now in NorthAdmin available only backend/API part,**

## Requirements

 - Python 3.11+
 - [FastAPI](https://github.com/tiangolo/fastapi) and [SQLAlclhemy](https://github.com/sqlalchemy/sqlalchemy)
 - Any async DB driver like [AsyncPG](https://github.com/MagicStack/asyncpg)
 - Any ASGI Python server like [Uvicorn](https://github.com/encode/uvicorn)

## Key benefits

 - **Easy to integrate** - The amount of code that needs to be completed for the integration of the admin panel is minimal.
 - **Fast** - NorthAdmin using async DB drivers and Swelte as UI framework to make admin panel as fast as possible.
 - **PWA** - Similar solutions are offered by SSR, which is slower, less convenient and creates additional load on the server.
 - **Flexibility** - We can create almost any filters to expand the functionality of the admin panel.
 - **Good-looking** - Modern Material UI-based interface thanks to [TailWindCSS](https://tailwindcss.com/)

## Example

Let's assume that we have project with:

 - Postgres
 - Some SQLAlchemy models 

In this example we prefer to use AsyncPG as driver.

### Install NorthAdmin

**Poetry**:

```bash
poetry add sqlalchemy asyncpg uvicorn north_admin
```

**PIP**

```bash
pip3 install sqlalchemy asyncpg uvicorn north_admin
pip3 freezee -> requirements.txt
```

### Add NorthAdmin in projects

For example, this is our `User` table look like:

```python
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(nullable=False)
    fullname: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[dt] = mapped_column(default=dt.now, server_default=func.current_timestamp())
```


Suppose we need the ability:
 - To view a list of users
 - To get detailed information about each of them
 - Soft delete (block) them
 - We can do it only with non-admin users (User.user_type == UserType.user)

**This is an artificial one-line example.**

If you need a more complete production-ready example, see [NorthAdmin Test App](https://github.com/OlenEnkeli/north_admin_testapp)

So, here an out `admin.py` file:

```python
from datetime import datetime as dt
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import bindparam, and_, select, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import ENUM
from north_admin import (
    NorthAdmin,
    FilterGroup,
    Filter,
    FieldType,
    AdminRouter,
    AdminMethods,
    AuthProvider,
    setup_admin,
    UserReturnSchema,
)
from north_admin.types import ModelType, QueryType


class Base(DeclarativeBase):
    pass


class UserType(str, Enum):
    USER = 'user'
    ADMIN = 'admin'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(nullable=False)
    fullname: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    user_type: Mapped[UserType] = mapped_column(ENUM(UserType, name='user_type'), default=UserType.USER)
    created_at: Mapped[dt] = mapped_column(default=dt.now, server_default=func.current_timestamp())


class AdminAuthProvider(AuthProvider):
    async def login(
        self,
        session: AsyncSession,
        login: str,
        password: str,
    ) -> User | None:
        query = (
            select(User)
            .filter(User.email == login)
            .filter(User.user_type == UserType.ADMIN)
        )

        return await session.scalar(query)

    async def get_user_by_id(
        self,
        session: AsyncSession,
        user_id: int | str,
    ) -> User | None:
        query = (
            select(User)
            .filter(User.id == user_id)
            .filter(User.user_type == UserType.ADMIN)
        )

        return await session.scalar(query)

    async def to_user_scheme(
        self,
        user: User,
    ) -> UserReturnSchema:
        return UserReturnSchema(
            id=user.id,
            login=user.email,
            fullname=user.fullname,
        )
    

admin_app = NorthAdmin(
    sqlalchemy_uri='postgresql+asyncpg://postgres:@127.0.0.1:5432/north_admin_test_app',
    jwt_secket_key='JNBjdejjn!w443@wer',
    auth_provider=AdminAuthProvider,
)

user_get_columns = [
    User.id,
    User.email,
    User.fullname,
    User.user_type,
    User.created_at,
]


def exclude_admin_users(query: QueryType) -> QueryType:
    query = query.filter(User.user_type != UserType.ADMIN)
    return query


admin_app.add_admin_routes(
    AdminRouter(
        model=User,
        model_title='Users',
        enabled_methods=[
            AdminMethods.GET_ONE,
            AdminMethods.GET_LIST,
            AdminMethods.SOFT_DELETE,
        ],
        process_query_method=exclude_admin_users,
        pkey_column=User.id,
        soft_delete_column=User.is_active,
        get_columns=user_get_columns,
        list_columns=user_get_columns,
        filters=[
            FilterGroup(
                query=(
                    and_(
                        User.created_at > dt.now().replace(hour=0, minute=0, second=0),
                        bindparam('created_today_param'),
                    )
                ),
                filters=[
                    Filter(
                        bindparam='created_today_param',
                        title='Created today',
                        field_type=FieldType.BOOLEAN,
                    ),
                ],
            ),
            FilterGroup(
                query=(User.created_at > bindparam('created_after_gt')),
                filters=[
                    Filter(
                        bindparam='created_after_gt',
                        title='Created after',
                        field_type=FieldType.DATETIME,
                    )
                ],
            ),
        ]
    )
)

app = FastAPI()

setup_admin(
    admin_app=admin_app,
    app=app,
)
```

Don't forget to use `Alembic` or other migration tools or `DeclarativeBase.Meta.create_all()` to create `User` table in DB

Short Example with psycopg:

Add this in the end of `admin.py`:

```python
if __name__ == '__main__':
    from sqlalchemy import create_engine


    Base.metadata.create_all(
        bind=create_engine(
            'postgresql+psycopg://postgres:@127.10.0.1:5432/north_admin_test_app'
        ),
    )
```

Install pscyopg and run it:

```bash
poetry add psycopg psycopg-binary
python3 -m admin
```



**Now we finally can run it**:

```bash
poetry run uvicorn north_admin.test_app:app --host 0.0.0.0 --port 8000 --reload
```

### Let's take a look at what's going on here

- Firstly, we create `AdminAuthProvider`, what must implement three methods - `login`, `get_user_id`, `to_user_scheme`

  - `login` - get `User` by login and password 
  - `get_user_by_id` - get `User` by id
  - `to_user_schema` - dump `User` model to `UserReturnSchema`. 


- Next we create `NorthAdmin` application with 3 required parameters (`sqlalchemy_uri`, `jwt_secket_key` and `auth_provider` - we just created it before)


- Now we can add admin page to our admin panel (`add_admin_routes` methods)

### Admin Router parameters:

 - `model` - SQLAlchemy model we want to administrate (**required**)

 - `model_title` - Verbose title (displayed in UI). By default generate from `model`

 - `emoji` - Emoji displayed near to model name in UI. By default - random emoji.

 - `enabled_methods` - List of actions, awailable in admin panel (`GET_LIST`, `GET_ONE`, `CREATE`, `UPDATE`, `DELETE`, `SOFT_DELETE`). By default - all ot them.

 - `process_query_method` - Function applied to SQLAlchemy query in (`GET_LIST`, `GET_ONE`, `UPDATE`, `DELETE`, `SOFT_DELETE`) methods. Feel free to excluding, filtering, etc.

 - `pkey_column` - Primary Key column. By default `model.id`

 - `list_columns` - Columns displayed when displaying a list of `model` items in UI. By default - all columns. 

 - `get_columns` - Similary for viewing one item. By default - all columns.

 - `create_columns` - Similary for creatine new item. By default - all non-key columns.

 - `update_columns` - Similary for updatings existing item. By default - all non-key columns.

 - `soft_delete_column` - Boolean SQLAlchemy column. When soft deleting (blocking) item, it set to `False`, is restoring to `True`. **Required**, if you have `SOFT_DELETE` in `enabled_methods`

 - `sortable_columns` - List of SQLAclehmy columns, A list of columns to which we can apply sorting in the UI. By default - all key column. (See `sort_by` params in list method)

 - `filters` - list of `FilterGroup` object. By default no filters applied.


### Filters

Filters are represented by `FilterGroup` and `Filter` classes

`FilterGroup` contains SQLAlchemy query with some `bind_params`.

Value of `bind_params` is represented in `Filter` `title` field and this is exactly the parameter that the front-end will.

Also `Filter` object contains name of filter in UI (`title`) and UI type (`field_type`)

In our case, we will see two filters in the admin panel:

 - Checkbox `Created Today`
 - Date-picker `Created After`

Awailable `FieldType`: `INTEGER`, `BOOLEAN` (checkbox), `FLOAT`, `STRING`, `ENUM` (listpicker), `DATETIME` (datetime picker), `ARRAY` (several string input)


**Filter system it may seem confusing (overcomplex) at the beginning, but it gives unlimited variability of implemented filters.**

### Result

Restart FastAPI application and **admin panel is ready**.

E.q. we running app with Uvicorn on http://127.0.0.1 we have:

 - Admin Panel UI in http://127.0.0.1/admin/
 - Admin Panel API in http://127.0.0.1/admin/api/
 - Swagger in http://127.0.0.1/admin/docs/

Create user with `user_type=UserType.Admin`, check out Swagger and **enjoy using your new admin panel**.
