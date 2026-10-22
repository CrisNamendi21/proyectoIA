"""Prevent duplicate curriculum contents.

Revision ID: f6e6cb9d9598
Revises: c040b61622ed
Create Date: 2026-10-22 13:38:13.385129

"""
from collections.abc import Sequence

from alembic import op
# revision identifiers, used by Alembic.
revision: str = "f6e6cb9d9598"
down_revision: str | Sequence[str] | None = "c040b61622ed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_curriculum_contents_grade_subject_description",
        "curriculum_contents",
        ["grade_id", "subject_id", "description"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_curriculum_contents_grade_subject_description",
        "curriculum_contents",
        type_="unique",
    )
