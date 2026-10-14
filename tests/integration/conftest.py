"""Fixtures propias: cada caso usa exclusivamente una base PostgreSQL nueva."""

from dataclasses import dataclass
import os
import re
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url


@dataclass
class FlowEnvironment:
    app: object
    engine: Engine
    teacher_id: int
    second_teacher_id: int
    grade_id: int
    other_grade_id: int
    subject_id: int
    other_subject_id: int
    content_id: int


@pytest.fixture
def flow_environment(monkeypatch):
    from app.core.config import get_settings
    from app.core.security import hash_password
    from app.db.base import Base
    from app.db.session import get_db_session
    from app.main import create_app
    from app.models import CurriculumContent, Grade, Subject, User
    from sqlalchemy.orm import sessionmaker

    admin_url = make_url(os.environ["COLEGIO_ALFA_INTEGRATION_ADMIN_URL"])
    assert admin_url.drivername == "postgresql+psycopg"
    assert admin_url.database == "postgres"
    assert admin_url.host in {"127.0.0.1", "localhost"}
    name = f"colegio_alfa_ai_flow_test_{uuid4().hex}"
    assert re.fullmatch(r"colegio_alfa_ai_flow_test_[0-9a-f]{32}", name)
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    engine = create_engine(admin_url.set(database=name))
    created = False
    app = None
    try:
        with admin.connect() as connection:
            assert connection.execute(text("SELECT current_database()")).scalar_one() == "postgres"
            connection.execute(text(f'CREATE DATABASE "{name}"'))
            created = True
        Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        with sessions() as session:
            password_hash = hash_password("clave-ficticia-integracion")
            teacher = User(username="docente_a_ficticio", password_hash=password_hash, is_active=True)
            second = User(username="docente_b_ficticio", password_hash=password_hash, is_active=True)
            inactive = User(username="docente_inactivo_ficticio", password_hash=password_hash, is_active=False)
            grade = Grade(name="Quinto grado")
            other_grade = Grade(name="Sexto grado")
            subject = Subject(name="Matemática")
            other_subject = Subject(name="Lengua")
            session.add_all([teacher, second, inactive, grade, other_grade, subject, other_subject])
            session.flush()
            curriculum = CurriculumContent(
                grade_id=grade.id, subject_id=subject.id, description="Fracciones equivalentes",
            )
            session.add(curriculum)
            session.commit()
        get_settings.cache_clear()
        app = create_app()

        def disposable_session():
            with sessions() as session:
                yield session

        app.dependency_overrides[get_db_session] = disposable_session
        yield FlowEnvironment(
            app, engine, teacher.id, second.id, grade.id, other_grade.id,
            subject.id, other_subject.id, curriculum.id,
        )
    finally:
        if app is not None:
            app.dependency_overrides.clear()
        engine.dispose()
        if created:
            with admin.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()
        get_settings.cache_clear()
