
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.grade import Grade
    from app.models.planning import Planning
    from app.models.subject import Subject


user_grades = Table(
    "user_grades",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("grade_id", ForeignKey("grades.id", ondelete="CASCADE"), primary_key=True),
)


user_subjects = Table(
    "user_subjects",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("subject_id", ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    profile_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    plannings: Mapped[list["Planning"]] = relationship(back_populates="user")
    grades: Mapped[list["Grade"]] = relationship(
        secondary=user_grades, back_populates="users"
    )
    subjects: Mapped[list["Subject"]] = relationship(
        secondary=user_subjects, back_populates="users"
    )
