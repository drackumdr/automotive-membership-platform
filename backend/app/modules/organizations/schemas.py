import uuid

from pydantic import BaseModel, ConfigDict, Field

ORG_TYPE_PATTERN = "^(CORPORATE|OWNED_WORKSHOP|AFFILIATE_WORKSHOP|FRANCHISE)$"


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str = Field(pattern=ORG_TYPE_PATTERN)
    parent_id: uuid.UUID | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, pattern="^(ACTIVE|INACTIVE)$")


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: str
    status: str
    parent_id: uuid.UUID | None


class BranchCreate(BaseModel):
    organization_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    address: str | None = Field(default=None, max_length=300)


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, max_length=300)


class BranchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    address: str | None
