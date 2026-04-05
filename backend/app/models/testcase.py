import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    test_task_id: Mapped[str] = mapped_column(
        ForeignKey("test_tasks.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    preconditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[str] = mapped_column(Text, nullable=False)
    actual_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, running, passed, failed, blocked
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    test_task: Mapped["TestTask"] = relationship(back_populates="test_cases")
    coverages: Mapped[list["ClauseCoverage"]] = relationship(
        back_populates="test_case", cascade="all, delete-orphan"
    )


class ClauseCoverage(Base):
    __tablename__ = "clause_coverage"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    clause_id: Mapped[str] = mapped_column(
        ForeignKey("spec_clauses.id", ondelete="CASCADE"), nullable=False
    )
    test_case_id: Mapped[str] = mapped_column(
        ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    clause: Mapped["SpecClause"] = relationship(back_populates="coverages")
    test_case: Mapped["TestCase"] = relationship(back_populates="coverages")
