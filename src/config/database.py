from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///"
engine = create_engine(DATABASE_URL, echo=False, conncet_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session() as session:
        yield session