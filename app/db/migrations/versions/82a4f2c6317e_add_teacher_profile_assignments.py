"""Add teacher profile assignments.

Revision ID: 82a4f2c6317e
Revises: f6e6cb9d9598
Create Date: 2026-10-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "82a4f2c6317e"
down_revision: str | Sequence[str] | None = "f6e6cb9d9598"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("profile_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "user_grades",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("grade_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["grade_id"], ["grades.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "grade_id"),
    )
    op.create_table(
        "user_subjects",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "subject_id"),
    )


def downgrade() -> None:
    op.drop_table("user_subjects")
    op.drop_table("user_grades")
    op.drop_column("users", "profile_completed_at")
