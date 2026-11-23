import re
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,60}$")
Password = Field(min_length=10, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(max_length=254)
    password: str = Field(max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str = Password


class PasswordRecovery(BaseModel):
    identifier: str = Field(max_length=254)


class RoleAssignmentIn(BaseModel):
    role: str
    organization_id: uuid.UUID | None = None


class RoleAssignmentOut(BaseModel):
    id: uuid.UUID
    role: str
    organization_id: uuid.UUID | None


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    username: str
    email: str | None = Field(default=None, max_length=254)
    password: str = Password
    roles: list[RoleAssignmentIn] = Field(min_length=1)

    @field_validator("username")
    @classmethod
    def _username(cls, v: str) -> str:
        v = v.strip().lower()
        if not USERNAME_RE.match(v):
            raise ValueError("usuario: 3-60 caracteres [a-z0-9._-]")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("correo inválido")
        return v


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, pattern="^(ACTIVE|DISABLED)$")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    username: str
    email: str | None
    status: str
    roles: list[RoleAssignmentOut] = []


class GrantOut(BaseModel):
    role: str
    organization_id: uuid.UUID | None
    permissions: list[str]


class MeOut(BaseModel):
    id: uuid.UUID
    name: str
    username: str
    grants: list[GrantOut]


class RoleOut(BaseModel):
    name: str
    description: str | None
    permissions: list[str]
