"""Service layer for requirement coverage calculation and sufficiency checks."""

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import Requirement
from app.models.specification import Specification, SpecVersion, SpecClause
from app.models.testcase import ClauseCoverage, TestCase


async def get_requirement_coverage(
    db: AsyncSession, requirement_id: str
) -> dict:
    """
    Calculate test coverage per severity level for a requirement.

    Returns a dict with:
        total_clauses, covered_clauses,
        must_coverage_pct, should_coverage_pct, may_coverage_pct,
        uncovered_clauses (list of clause dicts)
    """
    # Verify requirement exists
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalars().first()
    if requirement is None:
        raise ValueError(f"Requirement '{requirement_id}' not found")

    # Find all locked spec versions for this requirement
    spec_ids_query = (
        select(Specification.id)
        .where(Specification.requirement_id == requirement_id)
    )
    spec_result = await db.execute(spec_ids_query)
    spec_ids = [row[0] for row in spec_result.all()]

    if not spec_ids:
        return {
            "total_clauses": 0,
            "covered_clauses": 0,
            "must_coverage_pct": 0.0,
            "should_coverage_pct": 0.0,
            "may_coverage_pct": 0.0,
            "uncovered_clauses": [],
        }

    # Get locked version IDs
    version_ids_query = (
        select(SpecVersion.id)
        .where(
            and_(
                SpecVersion.spec_id.in_(spec_ids),
                SpecVersion.status == "locked",
            )
        )
    )
    version_result = await db.execute(version_ids_query)
    version_ids = [row[0] for row in version_result.all()]

    if not version_ids:
        return {
            "total_clauses": 0,
            "covered_clauses": 0,
            "must_coverage_pct": 0.0,
            "should_coverage_pct": 0.0,
            "may_coverage_pct": 0.0,
            "uncovered_clauses": [],
        }

    # Fetch all clauses from locked versions
    clauses_result = await db.execute(
        select(SpecClause).where(
            SpecClause.spec_version_id.in_(version_ids)
        )
    )
    all_clauses = list(clauses_result.scalars().all())

    if not all_clauses:
        return {
            "total_clauses": 0,
            "covered_clauses": 0,
            "must_coverage_pct": 0.0,
            "should_coverage_pct": 0.0,
            "may_coverage_pct": 0.0,
            "uncovered_clauses": [],
        }

    # Get clause IDs that have at least one coverage entry linked to a
    # non-blocked test case
    covered_clause_ids_result = await db.execute(
        select(ClauseCoverage.clause_id)
        .join(TestCase, ClauseCoverage.test_case_id == TestCase.id)
        .where(
            and_(
                ClauseCoverage.clause_id.in_([c.id for c in all_clauses]),
                TestCase.status.in_(["passed", "failed", "running", "pending"]),
            )
        )
        .distinct()
    )
    covered_clause_ids = {row[0] for row in covered_clause_ids_result.all()}

    # Compute per-severity stats
    severity_counts: dict[str, dict] = {}
    for sev in ("must", "should", "may"):
        severity_counts[sev] = {"total": 0, "covered": 0}

    uncovered_clauses = []
    for clause in all_clauses:
        sev = clause.severity
        severity_counts[sev]["total"] += 1
        if clause.id in covered_clause_ids:
            severity_counts[sev]["covered"] += 1
        else:
            uncovered_clauses.append(
                {
                    "id": clause.id,
                    "clause_id": clause.clause_id,
                    "title": clause.title,
                    "severity": clause.severity,
                    "category": clause.category,
                }
            )

    def _pct(covered: int, total: int) -> float:
        return round((covered / total) * 100, 2) if total > 0 else 0.0

    return {
        "total_clauses": len(all_clauses),
        "covered_clauses": len(covered_clause_ids),
        "must_coverage_pct": _pct(
            severity_counts["must"]["covered"],
            severity_counts["must"]["total"],
        ),
        "should_coverage_pct": _pct(
            severity_counts["should"]["covered"],
            severity_counts["should"]["total"],
        ),
        "may_coverage_pct": _pct(
            severity_counts["may"]["covered"],
            severity_counts["may"]["total"],
        ),
        "uncovered_clauses": uncovered_clauses,
    }


async def check_coverage_sufficient(
    db: AsyncSession, requirement_id: str
) -> bool:
    """
    Check whether coverage meets the minimum thresholds:
        must: 100%, should: >= 80%, may: not enforced.
    """
    coverage = await get_requirement_coverage(db, requirement_id)

    if coverage["total_clauses"] == 0:
        return True

    if coverage["must_coverage_pct"] < 100.0:
        return False

    # Only enforce should threshold when should clauses exist
    has_should = any(
        c["severity"] == "should" for c in coverage["uncovered_clauses"]
    ) or coverage["should_coverage_pct"] > 0.0

    if has_should and coverage["should_coverage_pct"] < 80.0:
        return False

    return True
