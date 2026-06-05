from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "postgresql+psycopg2://developer:1234567890@localhost:5432/dev_db"
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session(engine) as session:
        yield session