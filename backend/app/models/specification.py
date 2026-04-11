import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Specification(Base):
    __tablename__ = "specifications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    requirement_id: Mapped[str] = mapped_column(
        ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    spec_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # api, data, flow, ui, rule, security, event, config
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    requirement: Mapped["Requirement"] = relationship(back_populates="specifications")
    versions: Mapped[list["SpecVersion"]] = relationship(
        back_populates="specification", cascade="all, delete-orphan"
    )


class SpecVersion(Base):
    __tablename__ = "spec_versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    spec_id: Mapped[str] = mapped_column(
        ForeignKey("specifications.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft, reviewing, locked
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    locked_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    specification: Mapped["Specification"] = relationship(back_populates="versions")
    locker: Mapped["User | None"] = relationship(foreign_keys=[locked_by])
    clauses: Mapped[list["SpecClause"]] = relationship(
        back_populates="spec_version", cascade="all, delete-orphan"
    )
    dev_tasks: Mapped[list["DevTask"]] = relationship(back_populates="spec_version")


class SpecClause(Base):
    __tablename__ = "spec_clauses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    spec_version_id: Mapped[str] = mapped_column(
        ForeignKey("spec_versions.id", ondelete="CASCADE"), nullable=False
    )
    clause_id: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # auto-generated, e.g. "API-001"
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # functional, validation, security, performance, ui_element
    severity: Mapped[str] = mapped_column(
        String(10), nullable=False, default="must"
    )  # must, should, may
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    spec_version: Mapped["SpecVersion"] = relationship(back_populates="clauses")
    coverages: Mapped[list["ClauseCoverage"]] = relationship(
        back_populates="clause", cascade="all, delete-orphan"
    )
