"""NorthAdmin main module.

NorthAdmin is easy-to-setup PWA Admin Panel solution based on FastAPI, async SQLAlchemy and pre-render Swelte UI.
"""

from .admin_router import AdminRouter
from .app import NorthAdmin, setup_admin
from .auth_provider import AuthProvider
from .dto import FilterDTO, UserReturnSchema
from .filters import Filter, FilterGroup
from .types import AdminMethods, FieldType


__all__ = [
    "AdminMethods",
    "AdminRouter",
    "AuthProvider",
    "NorthAdmin",
    "setup_admin",
    "FilterDTO",
    "FieldType",
    "UserReturnSchema",
    "Filter",
    "FilterGroup",
]
