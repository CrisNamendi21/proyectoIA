import app.models  # noqa: F401
from app.db.base import Base


def test_shared_models_keep_the_agreed_relational_contract() -> None:
    tables = Base.metadata.tables
    assert set(tables) == {
        "users",
        "grades",
        "subjects",
        "curriculum_contents",
        "plannings",
        "user_grades",
        "user_subjects",
    }

    foreign_keys = {
        (table.name, foreign_key.parent.name, foreign_key.target_fullname)
        for table in tables.values()
        for foreign_key in table.foreign_keys
    }
    assert foreign_keys == {
        ("curriculum_contents", "grade_id", "grades.id"),
        ("curriculum_contents", "subject_id", "subjects.id"),
        ("plannings", "user_id", "users.id"),
        ("plannings", "grade_id", "grades.id"),
        ("plannings", "subject_id", "subjects.id"),
        ("plannings", "curriculum_content_id", "curriculum_contents.id"),
        ("user_grades", "user_id", "users.id"),
        ("user_grades", "grade_id", "grades.id"),
        ("user_subjects", "user_id", "users.id"),
        ("user_subjects", "subject_id", "subjects.id"),
    }

    assert not tables["users"].c.username.nullable
    assert tables["users"].c.username.unique
    assert not tables["plannings"].c.user_id.nullable
    assert not tables["plannings"].c.content.nullable
    assert tables["plannings"].c.grade_id.nullable
    assert tables["plannings"].c.subject_id.nullable
    assert tables["plannings"].c.curriculum_content_id.nullable
    assert tables["users"].c.profile_completed_at.nullable
