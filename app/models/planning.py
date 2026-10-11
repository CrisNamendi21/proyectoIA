
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.curriculum_content import CurriculumContent
    from app.models.grade import Grade
    from app.models.subject import Subject
    from app.models.user import User


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Planning(Base):
    __tablename__ = "plannings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    grade_id: Mapped[int | None] = mapped_column(ForeignKey("grades.id"), index=True)
    subject_id: Mapped[int | None] = mapped_column(
        ForeignKey("subjects.id"), index=True
    )
    curriculum_content_id: Mapped[int | None] = mapped_column(
        ForeignKey("curriculum_contents.id"), index=True
    )
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    user: Mapped["User"] = relationship(back_populates="plannings")
    grade: Mapped["Grade | None"] = relationship(back_populates="plannings")
    subject: Mapped["Subject | None"] = relationship(back_populates="plannings")
    curriculum_content: Mapped["CurriculumContent | None"] = relationship(
        back_populates="plannings"
    )
