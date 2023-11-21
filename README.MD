# NorthAdmin

Easy-to-setup PWA Admin Panel solution based on FastAPI, async SQLAlchemy and pre-render Swelte UI.


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

For example, this is our `User` table (`app/models/user.py`):

```python
from datetime import datetime as dt

from app.core.db import Base


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

And `Post` table (`app/models/post.py`)

```python
from datetime import datetime as dt

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY

from app.core.db import Base



class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    tags: Mapped[list[int]] = mapped_column(ARRAY(String), nullable=True)
    text: Mapped[str] = mapped_column(nullable=False)
    is_published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[dt] = mapped_column(default=dt.now, server_default=func.current_timestamp())
```

Suppose we need the ability:
 - to view a list of users
 - to get detailed information about each of them
 - soft delete (block) them
 - Create, view, get_list, update, delete and soft delete a posts

So, here an out `app/admin.py` file:

```python
from datetime import datetime as dt

from sqlalchemy import bindparam, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from north_admin import (
    NorthAdmin,
    FilterGroup,
    Filter,
    FieldType,
    AdminRouter,
    AdminMethods,
    AuthProvider,
)
from north_admin.types import ModelType

from app.models.user import User
from app.models.post import Post


class AdminAuthProvider(AuthProvider):
    async def login(
        self,
        session: AsyncSession,
        login: str,
        password: str,
    ) -> ModelType | None:
        query = (
            select(User)
            .filter(User.email == login)
            .filter(User.is_admin.is_(True))
        )

        return await session.scalar(query)

    async def get_user_by_id(
        self,
        session: AsyncSession,
        user_id: int | str,
    ) -> ModelType | None:
        query = (
            select(User)
            .filter(User.id == user_id)
            .filter(User.is_admin.is_(True))
        )

        return await session.scalar(query)


admin_app = NorthAdmin(
    sqlalchemy_uri='postgresql+asyncpg://postgres:@127.0.0.1:5432/north_admin_test_app',
    jwt_secket_key='JNBjdejjn!w443@wer',
    auth_provider=AdminAuthProvider,
)

user_get_columns = [User.id, User.email, User.fullname, User.is_active, User.created_at]

admin_app.add_admin_routes(
    AdminRouter(
        model=User,
        model_title='Users',
        enabled_methods=[AdminMethods.GET_ONE, AdminMethods.GET_LIST, AdminMethods.SOFT_DELETE],
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

admin_app.add_admin_routes(
    model=Post,
    model_title='Posts',
    pkey_column=Post.id,
    soft_delete_column=Post.is_published,
)

```

And also we need to setup admin panel in FastAPI main file (e.q. `app/app.py`)

```python
from north_admin import setup_admin

from app.admin import admin_app


setup_admin(
    app=app,
    admin_app=admin_app,
)
```

### Let's take a look at what's going on here

- Firstly, we create `AdminAuthProvider`, what must implement two methods - `login` and `get_user_id`

- Next we create `NorthAdmin` application with 3 required parameters (`sqlalchemy_uri`, `jwt_secket_key` and `auth_provider` - we just created it before)

- Now we can add admin page to our admin panel (`add_admin_routes` methods)

Let`s take a look at parameters:

 - `model` - SQLAlchemy model we want to administrate (**required**)
 - `model_title` - Verbose title (displayed in UI). By default generate from `model`
 - `emoji` - Emoji displayed near to model name in UI. By default - random emoji.
 - `enabled_methods` - List of actions, awailable in admin panel (`GET_LIST`, `GET_ONE`, `CREATE`, `UPDATE`, `DELETE`, `SOFT_DELETE`). By default all ot them.
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

Create user with `is_admin=True` flag, check out Swagger and **enjoy using your new admin panel**.
