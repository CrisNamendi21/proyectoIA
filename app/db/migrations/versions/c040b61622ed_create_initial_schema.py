"""Create the initial Colegio Alfa schema.

Revision ID: c040b61622ed
Revises:
Create Date: 2026-10-22 13:37:54.242509

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c040b61622ed"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_grades_name"), "grades", ["name"], unique=True)
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subjects_name"), "subjects", ["name"], unique=True)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_table(
        "curriculum_contents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("grade_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["grade_id"], ["grades.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_curriculum_contents_grade_id"),
        "curriculum_contents",
        ["grade_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_curriculum_contents_subject_id"),
        "curriculum_contents",
        ["subject_id"],
        unique=False,
    )
    op.create_table(
        "plannings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("grade_id", sa.Integer(), nullable=True),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column("curriculum_content_id", sa.Integer(), nullable=True),
        sa.Column(
            "content", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["curriculum_content_id"], ["curriculum_contents.id"]
        ),
        sa.ForeignKeyConstraint(["grade_id"], ["grades.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plannings_curriculum_content_id"),
        "plannings",
        ["curriculum_content_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_plannings_grade_id"),
        "plannings",
        ["grade_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_plannings_subject_id"),
        "plannings",
        ["subject_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_plannings_user_id"),
        "plannings",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_plannings_user_id"), table_name="plannings")
    op.drop_index(op.f("ix_plannings_subject_id"), table_name="plannings")
    op.drop_index(op.f("ix_plannings_grade_id"), table_name="plannings")
    op.drop_index(
        op.f("ix_plannings_curriculum_content_id"), table_name="plannings"
    )
    op.drop_table("plannings")
    op.drop_index(
        op.f("ix_curriculum_contents_subject_id"),
        table_name="curriculum_contents",
    )
    op.drop_index(
        op.f("ix_curriculum_contents_grade_id"),
        table_name="curriculum_contents",
    )
    op.drop_table("curriculum_contents")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_subjects_name"), table_name="subjects")
    op.drop_table("subjects")
    op.drop_index(op.f("ix_grades_name"), table_name="grades")
    op.drop_table("grades")
