

from north_admin import AdminMethods, AdminRouter, NorthAdmin
from north_admin.test_app import User
from north_admin.types import QueryType

from tests.models import UserType


def exclude_admin_users(query: QueryType) -> QueryType:
    return query.filter(User.user_type != UserType.ADMIN)


USER_GET_COLUMNS = [
    User.id,
    User.email,
    User.fullname,
    User.is_active,
    User.user_type,
    User.created_at,
]


def include_user_routes(app: NorthAdmin) -> NorthAdmin:
    app.add_admin_routes(
        AdminRouter(
            model=User,
            model_title="Users",
            enabled_methods=[
                AdminMethods.GET_ONE,
                AdminMethods.GET_LIST,
                AdminMethods.SOFT_DELETE,
                AdminMethods.DELETE,
            ],
            process_query_method=exclude_admin_users,
            pkey_column=User.id,
            soft_delete_column=User.is_active,
            get_columns=USER_GET_COLUMNS,
            list_columns=USER_GET_COLUMNS,
            sortable_columns=[User.id, User.email, User.is_active, User.created_at],
        ),
    )

    return app
