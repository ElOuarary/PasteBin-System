from enum import Enum

class Role(Enum, str):
    ADMIN = "admin"
    USER = "user"