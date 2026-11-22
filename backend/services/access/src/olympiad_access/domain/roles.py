"""Коды ролей аккаунтов."""

from enum import StrEnum


class RoleCode(StrEnum):
    ADMIN = "admin"
    AUTHOR = "author"
    REPRESENTATIVE = "representative"
    REVIEWER = "reviewer"
