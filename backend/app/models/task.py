import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DevTask(Base):
    __tablename__ = "dev_tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    requirement_id: Mapped[str] = mapped_column(
        ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    spec_version_id: Mapped[str] = mapped_column(
        ForeignKey("spec_versions.id", ondelete="SET NULL"), nullable=True
    )
    iteration_id: Mapped[str] = mapped_column(
        ForeignKey("iterations.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )  # open, in_progress, review, done, blocked
    assignee_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    estimate_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    requirement: Mapped["Requirement"] = relationship(back_populates="dev_tasks")
    spec_version: Mapped["SpecVersion | None"] = relationship(
        back_populates="dev_tasks"
    )
    iteration: Mapped["Iteration"] = relationship()
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assignee_id])


class TestTask(Base):
    __tablename__ = "test_tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    requirement_id: Mapped[str] = mapped_column(
        ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    iteration_id: Mapped[str] = mapped_column(
        ForeignKey("iterations.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )  # open, in_progress, review, done, blocked
    assignee_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    requirement: Mapped["Requirement"] = relationship(back_populates="test_tasks")
    iteration: Mapped["Iteration"] = relationship()
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assignee_id])
    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="test_task", cascade="all, delete-orphan"
    )
