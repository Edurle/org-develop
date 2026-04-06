"""Service layer for test case and clause coverage management."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.specification import SpecClause
from app.models.task import TestTask
from app.models.testcase import TestCase, ClauseCoverage
from app.services.audit import log_action

# Valid test case statuses
_TEST_CASE_STATUSES = {"pending", "running", "passed", "failed", "blocked"}

# Valid transitions for test case status
_TEST_CASE_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["running"],
    "running": ["passed", "failed", "blocked"],
    "passed": [],
    "failed": ["running"],
    "blocked": ["running"],
}


async def create_test_case(
    db: AsyncSession,
    test_task_id: str,
    title: str,
    preconditions: str | None,
    steps: str,
    expected_result: str,
    clause_ids: list[str],
    user_id: str | None = None,
) -> TestCase:
    """Create a test case and link it to the specified spec clauses."""
    # Verify test task exists
    result = await db.execute(
        select(TestTask).where(TestTask.id == test_task_id)
    )
    test_task = result.scalars().first()
    if test_task is None:
        raise ValueError(f"TestTask '{test_task_id}' not found")

    # Validate all clause_ids exist
    if clause_ids:
        result = await db.execute(
            select(SpecClause).where(SpecClause.id.in_(clause_ids))
        )
        found_clauses = result.scalars().all()
        found_ids = {c.id for c in found_clauses}

        missing = set(clause_ids) - found_ids
        if missing:
            raise ValueError(
                f"The following clause IDs do not exist: {sorted(missing)}"
            )

    # Create the test case
    test_case = TestCase(
        test_task_id=test_task_id,
        title=title,
        preconditions=preconditions,
        steps=steps,
        expected_result=expected_result,
        status="pending",
    )
    db.add(test_case)
    await db.flush()

    # Create ClauseCoverage entries
    for clause_id in clause_ids:
        coverage = ClauseCoverage(
            clause_id=clause_id,
            test_case_id=test_case.id,
        )
        db.add(coverage)

    await db.flush()
    await log_action(
        db, user_id=user_id, action="testcase.create",
        resource_type="test_case", resource_id=test_case.id,
        detail=f"Created test case '{title}'",
    )
    return test_case


async def update_test_case_status(
    db: AsyncSession,
    test_case_id: str,
    new_status: str,
    user_id: str | None = None,
) -> TestCase:
    """Update a test case's status with transition validation."""
    if new_status not in _TEST_CASE_STATUSES:
        raise ValueError(
            f"Invalid test case status '{new_status}'. "
            f"Must be one of: {', '.join(sorted(_TEST_CASE_STATUSES))}"
        )

    result = await db.execute(
        select(TestCase).where(TestCase.id == test_case_id)
    )
    test_case = result.scalars().first()
    if test_case is None:
        raise ValueError(f"TestCase '{test_case_id}' not found")

    if test_case.status == new_status:
        raise ValueError(
            f"Test case is already in '{new_status}' status"
        )

    allowed = _TEST_CASE_TRANSITIONS.get(test_case.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Invalid test case status transition: '{test_case.status}' -> "
            f"'{new_status}'. Allowed from '{test_case.status}': {allowed}"
        )

    test_case.status = new_status
    await db.flush()
    await db.refresh(test_case)
    await log_action(
        db, user_id=user_id, action="testcase.update_status",
        resource_type="test_case", resource_id=test_case.id,
        detail=f"Status changed to '{new_status}'",
    )
    return test_case


async def update_test_case(
    db: AsyncSession,
    test_case_id: str,
    user_id: str | None = None,
    title: str | None = None,
    preconditions: str | None = None,
    steps: str | None = None,
    expected_result: str | None = None,
    actual_result: str | None = None,
) -> TestCase:
    """Update editable fields on a test case."""
    result = await db.execute(
        select(TestCase).where(TestCase.id == test_case_id)
    )
    test_case = result.scalars().first()
    if test_case is None:
        raise ValueError(f"TestCase '{test_case_id}' not found")

    if title is not None:
        test_case.title = title
    if preconditions is not None:
        test_case.preconditions = preconditions
    if steps is not None:
        test_case.steps = steps
    if expected_result is not None:
        test_case.expected_result = expected_result
    if actual_result is not None:
        test_case.actual_result = actual_result

    await db.flush()
    await db.refresh(test_case)
    await log_action(
        db, user_id=user_id, action="testcase.update",
        resource_type="test_case", resource_id=test_case.id,
        detail=f"Updated test case '{test_case.title}'",
    )
    return test_case


async def delete_test_case(
    db: AsyncSession,
    test_case_id: str,
    user_id: str | None = None,
) -> None:
    """Delete a test case. Only allowed when status is 'pending'."""
    result = await db.execute(
        select(TestCase).where(TestCase.id == test_case_id)
    )
    test_case = result.scalars().first()
    if test_case is None:
        raise ValueError(f"TestCase '{test_case_id}' not found")

    if test_case.status != "pending":
        raise ValueError(
            f"Cannot delete test case in '{test_case.status}' status. "
            "Only 'pending' test cases can be deleted."
        )

    await log_action(
        db, user_id=user_id, action="testcase.delete",
        resource_type="test_case", resource_id=test_case.id,
        detail=f"Deleted test case '{test_case.title}'",
    )
    await db.delete(test_case)
    await db.flush()
