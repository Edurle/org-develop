import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    iteration_id: Mapped[str] = mapped_column(
        ForeignKey("iterations.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    priority: Mapped[str] = mapped_column(
        String(10), nullable=False, default="medium"
    )  # low, medium, high, critical
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft, spec_writing, spec_review, spec_locked, in_progress, testing, done, cancelled
    creator_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    assignee_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    iteration: Mapped["Iteration"] = relationship(back_populates="requirements")
    creator: Mapped["User"] = relationship(foreign_keys=[creator_id])
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assignee_id])
    specifications: Mapped[list["Specification"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
    dev_tasks: Mapped[list["DevTask"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
    test_tasks: Mapped[list["TestTask"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
