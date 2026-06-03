Using SQLModel for managing database with FastAPI app

SQLModel built on top SQLAlchemy and Pydantic

Object Relational Mapper are built by defining a class and inheriting
from the SQLModel class, then passing a arguement of table with the
value True

Using the Field class for the SQLModel frameworks help defining constraints
on the attributes of the object model representing the table

To Establish a connection to the database use the engine, investigate
the possible configuration that you can set for the connection

Each request need to have its own session so that request would not
access others

