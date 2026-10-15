"""Authentication and user management."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from core.exceptions import DuplicateError, NotFoundError, PermissionError as AppPermissionError, ValidationError
from core.ids import new_id
from core.permissions import has_permission
from core.validation import iso_now, required_text
from storage.csv_manager import CsvStore, Repository

hasher = PasswordHasher()

def hash_password(value: str) -> str:
    return hasher.hash(value)

def verify_password(hash_value: str, value: str) -> bool:
    try:
        hasher.verify(hash_value, value)
        return True
    except VerifyMismatchError:
        return False


class AuthService:
    def __init__(self, store: CsvStore, audit: "AuditService | None" = None):
        self.store = store
        self.users = Repository(store, "users.csv", "user_id")
        self.roles = Repository(store, "roles.csv", "role_id")
        self.role_permissions = Repository(store, "role_permissions.csv", "permission")
        self.audit = audit

    def seed_roles(self) -> None:
        existing = {r["name"] for r in self.roles.all()}
        from core.permissions import ROLE_PERMISSIONS
        for role_name in ROLE_PERMISSIONS:
            if role_name not in existing:
                self.roles.insert({
                    "role_id": new_id("role"),
                    "name": role_name,
                    "description": role_name,
                })
        existing_pairs = {(r["role_name"], r["permission"]) for r in self.role_permissions.all()}
        for role, perms in ROLE_PERMISSIONS.items():
            for perm in perms:
                if (role, perm) not in existing_pairs:
                    self.role_permissions.insert({"role_name": role, "permission": perm})

    def has_users(self) -> bool:
        return len(self.users.all()) > 0

    def create_user(self, actor: dict | None, username: str, full_name: str, role: str, password: str, is_active: bool = True) -> dict:
        if actor is not None and not has_permission(actor, "users.manage"):
            raise AppPermissionError("You do not have permission to create users.")
        username = required_text(username, "Username")
        if self.users.one(lambda r: r["username"].lower() == username.lower()):
            raise DuplicateError("Username already exists.")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        now = iso_now()
        row = {
            "user_id": new_id("usr"),
            "username": username,
            "full_name": full_name.strip(),
            "role": role,
            "password_hash": hasher.hash(password),
            "is_active": "true" if is_active else "false",
            "created_at": now,
            "updated_at": now,
            "last_login_at": "",
        }
        self.users.insert(row)
        if self.audit:
            self.audit.log((actor or {}).get("user_id", ""), "create_user", "user", row["user_id"], username)
        return row

    def ensure_first_admin(self, username: str = "admin", password: str = "ChangeMe123!") -> dict | None:
        self.seed_roles()
        if self.has_users():
            return None
        return self.create_user(None, username, "Administrator", "Administrator", password, True)

    def login(self, username: str, password: str) -> dict:
        user = self.users.one(lambda r: r["username"].lower() == required_text(username, "Username").lower())
        if not user:
            raise ValidationError("Invalid username or password.")
        if user.get("is_active", "").lower() != "true":
            raise ValidationError("This account is inactive.")
        try:
            hasher.verify(user["password_hash"], password)
        except VerifyMismatchError as exc:
            raise ValidationError("Invalid username or password.") from exc
        now = iso_now()
        self.users.update(user["user_id"], {"last_login_at": now})
        user["last_login_at"] = now
        user.pop("password_hash", None)
        return user

    def change_password(self, actor: dict, user_id: str, new_password: str) -> None:
        if actor.get("user_id") != user_id and not has_permission(actor, "users.manage"):
            raise AppPermissionError("You cannot change this password.")
        if len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found.")
        self.users.update(user_id, {"password_hash": hasher.hash(new_password), "updated_at": iso_now()})
        if self.audit:
            self.audit.log(actor.get("user_id", ""), "change_password", "user", user_id, "")

    def set_active(self, actor: dict, user_id: str, active: bool) -> None:
        if not has_permission(actor, "users.manage"):
            raise AppPermissionError("You do not have permission to manage users.")
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found.")
        self.users.update(user_id, {"is_active": "true" if active else "false", "updated_at": iso_now()})
        if self.audit:
            self.audit.log(actor.get("user_id", ""), "set_user_active", "user", user_id, str(active))