
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.curriculum_content import CurriculumContent
    from app.models.planning import Planning


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    curriculum_contents: Mapped[list["CurriculumContent"]] = relationship(
        back_populates="grade"
    )
    plannings: Mapped[list["Planning"]] = relationship(back_populates="grade")
