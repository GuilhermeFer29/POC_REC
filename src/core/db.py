from sqlmodel import create_engine, Session

from .settings import Settings


def create_session_maker(settings: Settings):
    engine = create_engine(settings.mysql_url, echo=False)

    def get_session():
        with Session(engine) as session:
            yield session

    return get_session
