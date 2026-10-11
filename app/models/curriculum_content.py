
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.grade import Grade
    from app.models.planning import Planning
    from app.models.subject import Subject


class CurriculumContent(Base):
    __tablename__ = "curriculum_contents"

    id: Mapped[int] = mapped_column(primary_key=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    description: Mapped[str] = mapped_column(Text)

    grade: Mapped["Grade"] = relationship(back_populates="curriculum_contents")
    subject: Mapped["Subject"] = relationship(back_populates="curriculum_contents")
    plannings: Mapped[list["Planning"]] = relationship(
        back_populates="curriculum_content"
    )
