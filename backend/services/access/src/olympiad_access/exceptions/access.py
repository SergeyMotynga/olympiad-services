"""Ошибки сценариев сервиса доступа."""


class AccessError(Exception):
    """Ошибка сценария доступа."""


class InvalidCredentials(AccessError):
    """Логин, пароль или токен не прошли проверку."""


class Forbidden(AccessError):
    """Для операции требуется другая роль."""


class InvalidAccountData(AccessError):
    """Логин или пароль имеет недопустимый формат."""


class DuplicateLogin(AccessError):
    """Логин уже занят."""


class AccountNotFound(AccessError):
    """Аккаунт с указанным идентификатором отсутствует."""


class AdminAlreadyExists(AccessError):
    """Первый администратор уже создан."""
