from accounts.models import User


def can_manage_notices(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.role in [User.Role.STAFF, User.Role.ADMIN]
