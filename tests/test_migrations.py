from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import UniqueConstraint

from app.db.base import Base
from app.models import CurriculumContent


def test_migration_history_has_one_head_matching_the_model() -> None:
    root = Path(__file__).resolve().parents[1]
    scripts = ScriptDirectory.from_config(Config(root / "alembic.ini"))

    assert scripts.get_heads() == ["f6e6cb9d9598"]
    assert scripts.get_revision("f6e6cb9d9598").down_revision == "c040b61622ed"

    table = Base.metadata.tables[CurriculumContent.__tablename__]
    constraint_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert "uq_curriculum_contents_grade_subject_description" in constraint_names
