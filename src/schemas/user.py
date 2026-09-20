from sqlmodel import SQLModel


class UserRegistryForm(SQLModel):
    username: str
    email: str
    password: str
