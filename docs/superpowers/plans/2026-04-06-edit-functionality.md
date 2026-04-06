# Edit Functionality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PATCH (edit) and DELETE endpoints for requirements, spec clauses, dev tasks, and test cases — both backend services/routes and frontend API/store/UI layers.

**Architecture:** Backend-first approach: add service methods, then router endpoints, then tests. Frontend follows: API functions, store actions, then UI modals with edit/delete buttons. All edits use modal dialogs (reuse existing `Modal` component). Delete uses confirmation dialog. Status guards prevent invalid deletes.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async (backend), Vue 3 + Pinia + UnoCSS (frontend), pytest-asyncio (tests)

---

## Task 1: Backend — Requirement update & delete service methods

**Files:**
- Modify: `backend/app/services/requirement.py`

- [ ] **Step 1: Add `update_requirement` and `delete_requirement` service methods**

In `backend/app/services/requirement.py`, add these two methods after the existing `create_requirement` function:

```python
async def update_requirement(
    db: AsyncSession,
    requirement_id: str,
    user_id: str,
    title: str | None = None,
    priority: str | None = None,
) -> Requirement:
    """Update editable fields of a requirement."""
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalars().first()
    if requirement is None:
        raise ValueError(f"Requirement '{requirement_id}' not found")

    if title is not None:
        requirement.title = title
    if priority is not None:
        if priority not in ("low", "medium", "high", "critical"):
            raise ValueError(
                f"Invalid priority '{priority}'. "
                "Must be one of: low, medium, high, critical"
            )
        requirement.priority = priority

    await db.flush()
    await log_action(
        db, user_id=user_id, action="requirement.update",
        resource_type="requirement", resource_id=requirement.id,
        detail=f"Updated requirement '{requirement.title}'",
    )
    await db.refresh(requirement)
    return requirement


async def delete_requirement(
    db: AsyncSession,
    requirement_id: str,
    user_id: str,
) -> None:
    """Delete a requirement (only draft or cancelled)."""
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalars().first()
    if requirement is None:
        raise ValueError(f"Requirement '{requirement_id}' not found")

    if requirement.status not in ("draft", "cancelled"):
        raise ValueError(
            f"Cannot delete requirement in '{requirement.status}' status. "
            "Only draft or cancelled requirements can be deleted."
        )

    await log_action(
        db, user_id=user_id, action="requirement.delete",
        resource_type="requirement", resource_id=requirement.id,
        detail=f"Deleted requirement '{requirement.title}'",
    )
    await db.delete(requirement)
    await db.flush()
```

- [ ] **Step 2: Verify imports are correct**

The file already imports `select`, `AsyncSession`, `Requirement`, `log_action`. The `update_requirement` and `delete_requirement` functions only use these existing imports. No new imports needed.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/requirement.py
git commit -m "feat: add update_requirement and delete_requirement service methods"
```

---

## Task 2: Backend — Requirement update & delete router endpoints

**Files:**
- Modify: `backend/app/routers/requirements.py`

- [ ] **Step 1: Update the existing `update_requirement` endpoint to use the service method**

The existing `PATCH /api/requirements/{requirement_id}` at line 82 does direct DB manipulation. Replace it to use the service method and add audit logging:

Replace the `update_requirement` route function (lines 82-103) with:

```python
@router.patch("/requirements/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: str,
    body: RequirementUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    # Only allow title and priority updates through this endpoint
    update_data = body.model_dump(exclude_unset=True)
    # Remove status and assignee_id — those go through dedicated endpoints
    update_data.pop("status", None)
    update_data.pop("assignee_id", None)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updatable fields provided",
        )
    try:
        req = await requirement_svc.update_requirement(
            db,
            requirement_id=requirement_id,
            user_id=user.id,
            title=update_data.get("title"),
            priority=update_data.get("priority"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return RequirementResponse.model_validate(req).model_dump()
```

- [ ] **Step 2: Add DELETE endpoint after the status transition endpoint (after line 131)**

```python
@router.delete(
    "/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_requirement(
    requirement_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        await requirement_svc.delete_requirement(
            db, requirement_id=requirement_id, user_id=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/requirements.py
git commit -m "feat: add requirement PATCH (field edit) and DELETE endpoints"
```

---

## Task 3: Backend — Spec clause update & delete

**Files:**
- Modify: `backend/app/services/clause.py`
- Modify: `backend/app/routers/specifications.py`

- [ ] **Step 1: Add `update_clause` and `delete_clause` to `backend/app/services/clause.py`**

Add these methods after the existing `list_clauses` function:

```python
async def update_clause(
    db: AsyncSession,
    clause_id: str,
    clause_id_str: str | None = None,
    title: str | None = None,
    description: str | None = None,
    category: str | None = None,
    severity: str | None = None,
) -> SpecClause:
    """Update a clause. Only allowed if the parent spec version is in draft status."""
    result = await db.execute(
        select(SpecClause).where(SpecClause.id == clause_id)
    )
    clause = result.scalars().first()
    if clause is None:
        raise ValueError(f"SpecClause '{clause_id}' not found")

    # Verify parent version is draft
    ver_result = await db.execute(
        select(SpecVersion).where(SpecVersion.id == clause.spec_version_id)
    )
    version = ver_result.scalars().first()
    if version is None:
        raise ValueError("Parent SpecVersion not found")
    if version.status != "draft":
        raise ValueError(
            f"Cannot edit clause: parent version status is '{version.status}', expected 'draft'"
        )

    if clause_id_str is not None:
        clause.clause_id = clause_id_str
    if title is not None:
        clause.title = title
    if description is not None:
        clause.description = description
    if category is not None:
        valid_categories = (
            "functional", "validation", "security", "performance", "ui_element",
        )
        if category not in valid_categories:
            raise ValueError(
                f"Invalid category '{category}'. "
                f"Must be one of: {', '.join(valid_categories)}"
            )
        clause.category = category
    if severity is not None:
        if severity not in ("must", "should", "may"):
            raise ValueError(
                f"Invalid severity '{severity}'. Must be one of: must, should, may"
            )
        clause.severity = severity

    await db.flush()
    await db.refresh(clause)
    return clause


async def delete_clause(
    db: AsyncSession,
    clause_id: str,
) -> None:
    """Delete a clause. Only allowed if the parent spec version is in draft status."""
    result = await db.execute(
        select(SpecClause).where(SpecClause.id == clause_id)
    )
    clause = result.scalars().first()
    if clause is None:
        raise ValueError(f"SpecClause '{clause_id}' not found")

    # Verify parent version is draft
    ver_result = await db.execute(
        select(SpecVersion).where(SpecVersion.id == clause.spec_version_id)
    )
    version = ver_result.scalars().first()
    if version is None:
        raise ValueError("Parent SpecVersion not found")
    if version.status != "draft":
        raise ValueError(
            f"Cannot delete clause: parent version status is '{version.status}', expected 'draft'"
        )

    await db.delete(clause)
    await db.flush()
```

Note: `SpecVersion` is already imported in `clause.py` at the top.

- [ ] **Step 2: Add PATCH and DELETE clause endpoints to `backend/app/routers/specifications.py`**

Add the `SpecClauseUpdate` import to the existing import block (line 12-18):

```python
from app.schemas.specification import (
    SpecificationCreate,
    SpecificationResponse,
    SpecVersionCreate,
    SpecVersionResponse,
    SpecClauseCreate,
    SpecClauseResponse,
    SpecClauseUpdate,
)
```

Then add these endpoints after the existing `list_clauses` endpoint (after line 213):

```python
@router.patch("/spec-clauses/{clause_id}", response_model=SpecClauseResponse)
async def update_clause(
    clause_id: str,
    body: SpecClauseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updatable fields provided",
        )
    try:
        clause = await clause_svc.update_clause(
            db,
            clause_id=clause_id,
            clause_id_str=update_data.get("clause_id"),
            title=update_data.get("title"),
            description=update_data.get("description"),
            category=update_data.get("category"),
            severity=update_data.get("severity"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="clause.update",
        resource_type="spec_clause", resource_id=clause.id,
        detail=f"Updated clause '{clause.clause_id}'",
    )
    return SpecClauseResponse.model_validate(clause).model_dump()


@router.delete(
    "/spec-clauses/{clause_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_clause(
    clause_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        await clause_svc.delete_clause(db, clause_id=clause_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="clause.delete",
        resource_type="spec_clause", resource_id=clause_id,
        detail=f"Deleted clause '{clause_id}'",
    )
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/clause.py backend/app/routers/specifications.py
git commit -m "feat: add clause update and delete service + endpoints"
```

---

## Task 4: Backend — Dev task update & delete

**Files:**
- Modify: `backend/app/services/task.py`
- Modify: `backend/app/routers/tasks.py`

- [ ] **Step 1: Add `update_dev_task` and `delete_dev_task` to `backend/app/services/task.py`**

Add these methods after `create_test_task`:

```python
async def update_dev_task(
    db: AsyncSession,
    task_id: str,
    title: str | None = None,
    estimate_hours: float | None = None,
    assignee_id: str | None = None,
) -> DevTask:
    """Update editable fields of a dev task."""
    result = await db.execute(
        select(DevTask).where(DevTask.id == task_id)
    )
    task = result.scalars().first()
    if task is None:
        raise ValueError(f"DevTask '{task_id}' not found")

    if title is not None:
        task.title = title
    if estimate_hours is not None:
        task.estimate_hours = estimate_hours
    if assignee_id is not None:
        task.assignee_id = assignee_id

    await db.flush()
    await db.refresh(task)
    return task


async def delete_dev_task(
    db: AsyncSession,
    task_id: str,
) -> None:
    """Delete a dev task (only open status)."""
    result = await db.execute(
        select(DevTask).where(DevTask.id == task_id)
    )
    task = result.scalars().first()
    if task is None:
        raise ValueError(f"DevTask '{task_id}' not found")

    if task.status != "open":
        raise ValueError(
            f"Cannot delete dev task in '{task.status}' status. "
            "Only open tasks can be deleted."
        )

    await db.delete(task)
    await db.flush()
```

- [ ] **Step 2: Add PATCH and DELETE dev task endpoints to `backend/app/routers/tasks.py`**

Add `DevTaskUpdate` to the existing import block:

```python
from app.schemas.task import (
    DevTaskCreate,
    DevTaskUpdate,
    DevTaskResponse,
    TestTaskCreate,
    TestTaskResponse,
)
```

Add these endpoints after `update_dev_task_status` (after line 110):

```python
@router.patch("/dev-tasks/{task_id}", response_model=DevTaskResponse)
async def update_dev_task(
    task_id: str,
    body: DevTaskUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    update_data = body.model_dump(exclude_unset=True)
    # Only allow title, estimate_hours, assignee_id through this endpoint
    update_data.pop("status", None)
    update_data.pop("spec_version_id", None)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updatable fields provided",
        )
    try:
        t = await task_svc.update_dev_task(
            db,
            task_id=task_id,
            title=update_data.get("title"),
            estimate_hours=update_data.get("estimate_hours"),
            assignee_id=update_data.get("assignee_id"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="task.dev.update",
        resource_type="dev_task", resource_id=t.id,
        detail=f"Updated dev task '{t.title}'",
    )
    return DevTaskResponse.model_validate(t).model_dump()


@router.delete(
    "/dev-tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dev_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        await task_svc.delete_dev_task(db, task_id=task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="task.dev.delete",
        resource_type="dev_task", resource_id=task_id,
        detail=f"Deleted dev task '{task_id}'",
    )
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/task.py backend/app/routers/tasks.py
git commit -m "feat: add dev task update and delete service + endpoints"
```

---

## Task 5: Backend — Test case update & delete

**Files:**
- Modify: `backend/app/services/testcase.py`
- Modify: `backend/app/routers/testcases.py`

- [ ] **Step 1: Add `update_test_case` and `delete_test_case` to `backend/app/services/testcase.py`**

Add these methods after `update_test_case_status`:

```python
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
    """Update editable fields of a test case."""
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
    """Delete a test case (only pending status)."""
    result = await db.execute(
        select(TestCase).where(TestCase.id == test_case_id)
    )
    test_case = result.scalars().first()
    if test_case is None:
        raise ValueError(f"TestCase '{test_case_id}' not found")

    if test_case.status != "pending":
        raise ValueError(
            f"Cannot delete test case in '{test_case.status}' status. "
            "Only pending test cases can be deleted."
        )

    await log_action(
        db, user_id=user_id, action="testcase.delete",
        resource_type="test_case", resource_id=test_case.id,
        detail=f"Deleted test case '{test_case.title}'",
    )
    await db.delete(test_case)
    await db.flush()
```

- [ ] **Step 2: Add PATCH and DELETE test case endpoints to `backend/app/routers/testcases.py`**

Add `TestCaseUpdate` to the import block:

```python
from app.schemas.testcase import TestCaseResponse, TestCaseUpdate
```

Add these endpoints after `update_test_case_status` (after line 91):

```python
@router.patch("/test-cases/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case(
    test_case_id: str,
    body: TestCaseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    update_data = body.model_dump(exclude_unset=True)
    # Only allow content fields through this endpoint, not status
    update_data.pop("status", None)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updatable fields provided",
        )
    try:
        tc = await testcase_svc.update_test_case(
            db,
            test_case_id=test_case_id,
            user_id=user.id,
            title=update_data.get("title"),
            preconditions=update_data.get("preconditions"),
            steps=update_data.get("steps"),
            expected_result=update_data.get("expected_result"),
            actual_result=update_data.get("actual_result"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return TestCaseResponse.model_validate(tc).model_dump()


@router.delete(
    "/test-cases/{test_case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_test_case(
    test_case_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        await testcase_svc.delete_test_case(
            db, test_case_id=test_case_id, user_id=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/testcase.py backend/app/routers/testcases.py
git commit -m "feat: add test case update and delete service + endpoints"
```

---

## Task 6: Backend — Tests for new service methods

**Files:**
- Create: `backend/tests/test_edit_functionality.py`

- [ ] **Step 1: Write comprehensive tests**

Create `backend/tests/test_edit_functionality.py`:

```python
"""Tests for edit and delete functionality across all entities."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.requirement import (
    create_requirement,
    update_requirement,
    delete_requirement,
    update_requirement_status,
)
from app.services.specification import (
    create_specification,
    create_spec_version,
    submit_spec_for_review,
    lock_spec,
)
from app.services.clause import create_clause, update_clause, delete_clause
from app.services.task import (
    create_dev_task,
    update_dev_task,
    delete_dev_task,
)
from app.services.testcase import (
    create_test_case,
    update_test_case,
    delete_test_case,
)


@pytest_asyncio.fixture
async def req_with_seed(db: AsyncSession, seed_data):
    req = await create_requirement(
        db,
        iteration_id=seed_data["iteration"].id,
        title="Edit Test Req",
        priority="medium",
        creator_id=seed_data["user"].id,
    )
    return {**seed_data, "requirement": req}


# ── Requirement ──


class TestRequirementEdit:

    async def test_update_title(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        updated = await update_requirement(db, req.id, uid, title="Updated Title")
        assert updated.title == "Updated Title"

    async def test_update_priority(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        updated = await update_requirement(db, req.id, uid, priority="critical")
        assert updated.priority == "critical"

    async def test_update_both_fields(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        updated = await update_requirement(db, req.id, uid, title="New", priority="high")
        assert updated.title == "New"
        assert updated.priority == "high"

    async def test_update_invalid_priority(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        with pytest.raises(ValueError, match="Invalid priority"):
            await update_requirement(db, req.id, uid, priority="invalid")

    async def test_update_nonexistent(self, db, req_with_seed):
        uid = req_with_seed["user"].id
        with pytest.raises(ValueError, match="not found"):
            await update_requirement(db, "nonexistent-id", uid, title="x")

    async def test_delete_draft(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        await delete_requirement(db, req.id, uid)
        with pytest.raises(ValueError, match="not found"):
            await update_requirement(db, req.id, uid, title="x")

    async def test_delete_non_draft_rejected(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req.id, "spec_writing", uid)
        with pytest.raises(ValueError, match="Only draft or cancelled"):
            await delete_requirement(db, req.id, uid)

    async def test_delete_cancelled(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        # Advance to spec_locked then cancel
        await update_requirement_status(db, req.id, "spec_writing", uid)
        spec = await create_specification(db, req.id, "api", "Spec")
        ver = await create_spec_version(db, spec.id, {"endpoints": []})
        await update_requirement_status(db, req.id, "spec_review", uid)
        await submit_spec_for_review(db, ver.id)
        await lock_spec(db, ver.id, uid)
        await update_requirement_status(db, req.id, "cancelled", uid)
        # Now delete should work
        await delete_requirement(db, req.id, uid)


# ── Clause ──


class TestClauseEdit:

    async def _setup_draft_version(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Test Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        return version

    async def test_update_clause_title(self, db, req_with_seed):
        version = await self._setup_draft_version(db, req_with_seed)
        clause = await create_clause(db, version.id, "FN-001", "Original", "Desc", "functional", "must")
        updated = await update_clause(db, clause.id, title="Updated Title")
        assert updated.title == "Updated Title"

    async def test_update_clause_severity(self, db, req_with_seed):
        version = await self._setup_draft_version(db, req_with_seed)
        clause = await create_clause(db, version.id, "FN-001", "Title", "Desc", "functional", "must")
        updated = await update_clause(db, clause.id, severity="should")
        assert updated.severity == "should"

    async def test_update_clause_all_fields(self, db, req_with_seed):
        version = await self._setup_draft_version(db, req_with_seed)
        clause = await create_clause(db, version.id, "FN-001", "Old", "Old desc", "functional", "must")
        updated = await update_clause(
            db, clause.id,
            clause_id_str="FN-002", title="New", description="New desc",
            category="security", severity="may",
        )
        assert updated.clause_id == "FN-002"
        assert updated.title == "New"
        assert updated.description == "New desc"
        assert updated.category == "security"
        assert updated.severity == "may"

    async def test_update_clause_locked_version_rejected(self, db, req_with_seed):
        version = await self._setup_draft_version(db, req_with_seed)
        uid = req_with_seed["user"].id
        clause = await create_clause(db, version.id, "FN-001", "Title", "Desc", "functional", "must")
        # Lock the version
        await submit_spec_for_review(db, version.id)
        await lock_spec(db, version.id, uid)
        with pytest.raises(ValueError, match="expected 'draft'"):
            await update_clause(db, clause.id, title="Should Fail")

    async def test_delete_clause_draft(self, db, req_with_seed):
        version = await self._setup_draft_version(db, req_with_seed)
        clause = await create_clause(db, version.id, "FN-001", "Title", "Desc", "functional", "must")
        await delete_clause(db, clause.id)
        # Verify deleted — trying to update should fail
        with pytest.raises(ValueError, match="not found"):
            await update_clause(db, clause.id, title="Should Fail")

    async def test_delete_clause_locked_version_rejected(self, db, req_with_seed):
        version = await self._setup_draft_version(db, req_with_seed)
        uid = req_with_seed["user"].id
        clause = await create_clause(db, version.id, "FN-001", "Title", "Desc", "functional", "must")
        await submit_spec_for_review(db, version.id)
        await lock_spec(db, version.id, uid)
        with pytest.raises(ValueError, match="expected 'draft'"):
            await delete_clause(db, clause.id)


# ── Dev Task ──


class TestDevTaskEdit:

    async def _setup_locked_req(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        await update_requirement_status(db, req_id, "spec_review", uid)
        await submit_spec_for_review(db, version.id)
        await lock_spec(db, version.id, uid)
        return version

    async def test_update_dev_task_title(self, db, req_with_seed):
        version = await self._setup_locked_req(db, req_with_seed)
        req_id = req_with_seed["requirement"].id
        iter_id = req_with_seed["iteration"].id
        task = await create_dev_task(db, req_id, version.id, iter_id, "Original Task")
        updated = await update_dev_task(db, task.id, title="Updated Task")
        assert updated.title == "Updated Task"

    async def test_update_dev_task_estimate(self, db, req_with_seed):
        version = await self._setup_locked_req(db, req_with_seed)
        req_id = req_with_seed["requirement"].id
        iter_id = req_with_seed["iteration"].id
        task = await create_dev_task(db, req_id, version.id, iter_id, "Task")
        updated = await update_dev_task(db, task.id, estimate_hours=8.0)
        assert updated.estimate_hours == 8.0

    async def test_delete_open_task(self, db, req_with_seed):
        version = await self._setup_locked_req(db, req_with_seed)
        req_id = req_with_seed["requirement"].id
        iter_id = req_with_seed["iteration"].id
        task = await create_dev_task(db, req_id, version.id, iter_id, "Task")
        await delete_dev_task(db, task.id)
        # Verify — trying to update should fail
        with pytest.raises(ValueError, match="not found"):
            await update_dev_task(db, task.id, title="Should Fail")

    async def test_delete_non_open_task_rejected(self, db, req_with_seed):
        version = await self._setup_locked_req(db, req_with_seed)
        req_id = req_with_seed["requirement"].id
        iter_id = req_with_seed["iteration"].id
        uid = req_with_seed["user"].id
        task = await create_dev_task(db, req_id, version.id, iter_id, "Task")
        # Claim the task so it's in_progress
        from app.services.task import claim_dev_task
        await claim_dev_task(db, task.id, uid)
        with pytest.raises(ValueError, match="Only open tasks"):
            await delete_dev_task(db, task.id)


# ── Test Case ──


class TestTestCaseEdit:

    async def _setup_test_task(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        iter_id = req_with_seed["iteration"].id
        from app.services.task import create_test_task
        task = await create_test_task(db, req_id, iter_id, "Test Task")
        return task

    async def test_update_test_case_title(self, db, req_with_seed):
        task = await self._setup_test_task(db, req_with_seed)
        tc = await create_test_case(db, task.id, "Original TC", None, "step 1", "pass", [])
        updated = await update_test_case(db, tc.id, title="Updated TC")
        assert updated.title == "Updated TC"

    async def test_update_test_case_fields(self, db, req_with_seed):
        task = await self._setup_test_task(db, req_with_seed)
        tc = await create_test_case(db, task.id, "TC", "pre", "step", "expected", [])
        updated = await update_test_case(
            db, tc.id,
            preconditions="new pre", steps="new step",
            expected_result="new expected", actual_result="new actual",
        )
        assert updated.preconditions == "new pre"
        assert updated.steps == "new step"
        assert updated.expected_result == "new expected"
        assert updated.actual_result == "new actual"

    async def test_delete_pending_test_case(self, db, req_with_seed):
        task = await self._setup_test_task(db, req_with_seed)
        tc = await create_test_case(db, task.id, "TC", None, "step", "expected", [])
        await delete_test_case(db, tc.id)
        with pytest.raises(ValueError, match="not found"):
            await update_test_case(db, tc.id, title="Should Fail")

    async def test_delete_non_pending_test_case_rejected(self, db, req_with_seed):
        task = await self._setup_test_task(db, req_with_seed)
        uid = req_with_seed["user"].id
        tc = await create_test_case(db, task.id, "TC", None, "step", "expected", [])
        # Move to running status
        from app.services.testcase import update_test_case_status
        await update_test_case_status(db, tc.id, "running", uid)
        with pytest.raises(ValueError, match="Only pending"):
            await delete_test_case(db, tc.id, uid)
```

- [ ] **Step 2: Run all tests**

```bash
cd backend && pytest tests/test_edit_functionality.py -v
```

Expected: All tests pass.

- [ ] **Step 3: Run full test suite**

```bash
cd backend && pytest -v
```

Expected: All existing + new tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_edit_functionality.py
git commit -m "test: add tests for edit and delete functionality"
```

---

## Task 7: Frontend — API endpoints

**Files:**
- Modify: `frontend/src/api/endpoints.ts`

- [ ] **Step 1: Add new API functions**

In `frontend/src/api/endpoints.ts`:

Add to `reqApi` object (after `updateStatus`):

```typescript
  update: (id: string, data: { title?: string; priority?: string }) =>
    api.patch<Requirement>(`/requirements/${id}`, data),
  delete: (id: string) =>
    api.delete(`/requirements/${id}`),
```

Add to `specApi` object (after `createClause`):

```typescript
  updateClause: (clauseId: string, data: {
    clause_id?: string; title?: string; description?: string
    category?: string; severity?: string
  }) =>
    api.patch<SpecClause>(`/spec-clauses/${clauseId}`, data),
  deleteClause: (clauseId: string) =>
    api.delete(`/spec-clauses/${clauseId}`),
```

Add to `taskApi` object (after `updateDevTaskStatus`):

```typescript
  updateDevTask: (taskId: string, data: {
    title?: string; estimate_hours?: number | null; assignee_id?: string | null
  }) =>
    api.patch<DevTask>(`/dev-tasks/${taskId}`, data),
  deleteDevTask: (taskId: string) =>
    api.delete(`/dev-tasks/${taskId}`),
```

Add to `tcApi` object (after `updateStatus`):

```typescript
  update: (tcId: string, data: {
    title?: string; preconditions?: string; steps?: string
    expected_result?: string; actual_result?: string
  }) =>
    api.patch<TestCase>(`/test-cases/${tcId}`, data),
  delete: (tcId: string) =>
    api.delete(`/test-cases/${tcId}`),
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/endpoints.ts
git commit -m "feat: add frontend API functions for edit and delete"
```

---

## Task 8: Frontend — Store actions

**Files:**
- Modify: `frontend/src/stores/requirement.ts`
- Modify: `frontend/src/stores/specification.ts`
- Modify: `frontend/src/stores/task.ts`
- Modify: `frontend/src/stores/testcase.ts`

- [ ] **Step 1: Add actions to requirement store**

In `frontend/src/stores/requirement.ts`, add these functions before the `return` statement:

```typescript
  async function update(id: string, data: { title?: string; priority?: string }) {
    const res = await reqApi.update(id, data)
    const idx = requirements.value.findIndex((r) => r.id === id)
    if (idx !== -1) requirements.value[idx] = res.data
    if (currentRequirement.value?.id === id) currentRequirement.value = res.data
    return res.data
  }

  async function remove(id: string) {
    await reqApi.delete(id)
    requirements.value = requirements.value.filter((r) => r.id !== id)
    if (currentRequirement.value?.id === id) currentRequirement.value = null
  }
```

Add `update, remove` to the return statement.

- [ ] **Step 2: Add actions to specification store**

In `frontend/src/stores/specification.ts`, add these functions before the `return` statement:

```typescript
  async function updateClause(id: string, data: {
    clause_id?: string; title?: string; description?: string
    category?: string; severity?: string
  }) {
    const res = await specApi.updateClause(id, data)
    const idx = clauses.value.findIndex((c) => c.id === id)
    if (idx !== -1) clauses.value[idx] = res.data
    return res.data
  }

  async function removeClause(id: string) {
    await specApi.deleteClause(id)
    clauses.value = clauses.value.filter((c) => c.id !== id)
  }
```

Add `updateClause, removeClause` to the return statement.

- [ ] **Step 3: Add actions to task store**

In `frontend/src/stores/task.ts`, add these functions before the `return` statement:

```typescript
  async function updateDevTask(id: string, data: {
    title?: string; estimate_hours?: number | null; assignee_id?: string | null
  }) {
    const res = await taskApi.updateDevTask(id, data)
    const idx = devTasks.value.findIndex((t) => t.id === id)
    if (idx !== -1) devTasks.value[idx] = res.data
    return res.data
  }

  async function removeDevTask(id: string) {
    await taskApi.deleteDevTask(id)
    devTasks.value = devTasks.value.filter((t) => t.id !== id)
  }
```

Add `updateDevTask, removeDevTask` to the return statement.

- [ ] **Step 4: Add actions to testcase store**

In `frontend/src/stores/testcase.ts`, add these functions before the `return` statement:

```typescript
  async function update(tcId: string, data: {
    title?: string; preconditions?: string; steps?: string
    expected_result?: string; actual_result?: string
  }) {
    const res = await tcApi.update(tcId, data)
    const idx = testCases.value.findIndex((tc) => tc.id === tcId)
    if (idx !== -1) testCases.value[idx] = res.data
    return res.data
  }

  async function remove(tcId: string) {
    await tcApi.delete(tcId)
    testCases.value = testCases.value.filter((tc) => tc.id !== tcId)
  }
```

Add `update, remove` to the return statement.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/stores/
git commit -m "feat: add update and remove actions to all stores"
```

---

## Task 9: Frontend — Requirement list view edit/delete UI

**Files:**
- Modify: `frontend/src/views/RequirementListView.vue`

- [ ] **Step 1: Add edit modal state and delete confirmation**

Add new refs after the existing modal refs (around line 35):

```typescript
// Edit requirement modal
const showEditModal = ref(false)
const editId = ref('')
const editTitle = ref('')
const editPriority = ref<Priority>('medium')

// Delete confirmation
const showDeleteConfirm = ref(false)
const deleteTargetId = ref('')
const deleteTargetTitle = ref('')
```

- [ ] **Step 2: Add handler functions**

Add these functions after `handleCreate`:

```typescript
function openEditModal(req: Requirement) {
  editId.value = req.id
  editTitle.value = req.title
  editPriority.value = req.priority
  showEditModal.value = true
}

async function handleEdit() {
  if (!editTitle.value.trim()) return
  try {
    await reqStore.update(editId.value, {
      title: editTitle.value.trim(),
      priority: editPriority.value,
    })
    showEditModal.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to update requirement'
  }
}

function openDeleteConfirm(req: Requirement) {
  deleteTargetId.value = req.id
  deleteTargetTitle.value = req.title
  showDeleteConfirm.value = true
}

async function handleDelete() {
  try {
    await reqStore.remove(deleteTargetId.value)
    showDeleteConfirm.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to delete requirement'
  }
}
```

Import `Requirement` type: add to the existing import line:
```typescript
import type { Priority, Requirement } from '@/types'
```

- [ ] **Step 3: Update table Actions column**

Replace the Actions column `<td>` (line 214-220) with:

```html
<td class="px-4 py-3">
  <div class="flex items-center gap-2">
    <button
      class="text-blue-600 hover:text-blue-800 text-xs font-semibold transition-colors"
      @click.stop="navigateToReq(req.id)"
    >
      View
    </button>
    <button
      class="text-gray-500 hover:text-gray-700 text-xs font-semibold transition-colors"
      @click.stop="openEditModal(req)"
    >
      Edit
    </button>
    <button
      v-if="req.status === 'draft' || req.status === 'cancelled'"
      class="text-red-500 hover:text-red-700 text-xs font-semibold transition-colors"
      @click.stop="openDeleteConfirm(req)"
    >
      Delete
    </button>
  </div>
</td>
```

- [ ] **Step 4: Add Edit Modal and Delete Confirmation Modal templates**

Add after the existing Create Requirement Modal (after line 280):

```html
<!-- Edit Requirement Modal -->
<Modal :show="showEditModal" title="Edit Requirement" @close="showEditModal = false">
  <div class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
      <input
        v-model="editTitle"
        type="text"
        placeholder="Requirement title"
        class="input-glass"
        @keyup.enter="handleEdit"
      />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Priority</label>
      <select v-model="editPriority" class="select-glass">
        <option v-for="p in priorityOptions" :key="p" :value="p">{{ p.charAt(0).toUpperCase() + p.slice(1) }}</option>
      </select>
    </div>
  </div>
  <div class="flex justify-end gap-3 mt-6">
    <button class="btn-secondary" @click="showEditModal = false">Cancel</button>
    <button class="btn-primary" :disabled="!editTitle.trim()" @click="handleEdit">Save</button>
  </div>
</Modal>

<!-- Delete Confirmation Modal -->
<Modal :show="showDeleteConfirm" title="Delete Requirement" @close="showDeleteConfirm = false">
  <p class="text-sm text-gray-600">
    Are you sure you want to delete <span class="font-semibold text-gray-900">{{ deleteTargetTitle }}</span>?
    This action cannot be undone.
  </p>
  <div class="flex justify-end gap-3 mt-6">
    <button class="btn-secondary" @click="showDeleteConfirm = false">Cancel</button>
    <button class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors" @click="handleDelete">Delete</button>
  </div>
</Modal>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/RequirementListView.vue
git commit -m "feat: add edit and delete UI to requirement list view"
```

---

## Task 10: Frontend — Requirement detail view edit/delete UI

**Files:**
- Modify: `frontend/src/views/RequirementDetailView.vue`

- [ ] **Step 1: Add edit/delete state for requirement header**

Add refs after existing modal refs (around line 48):

```typescript
// Edit requirement modal
const showEditReqModal = ref(false)
const editReqTitle = ref('')
const editReqPriority = ref<Priority>('medium')
```

Add `Priority` to the import:
```typescript
import type { SpecType, Priority } from '@/types'
```

- [ ] **Step 2: Add edit requirement handlers**

Add after existing handler functions:

```typescript
function openEditReqModal() {
  if (!currentReq.value) return
  editReqTitle.value = currentReq.value.title
  editReqPriority.value = currentReq.value.priority
  showEditReqModal.value = true
}

async function handleEditReq() {
  if (!editReqTitle.value.trim()) return
  try {
    await reqStore.update(currentReq.value!.id, {
      title: editReqTitle.value.trim(),
      priority: editReqPriority.value,
    })
    showEditReqModal.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to update requirement'
  }
}
```

- [ ] **Step 3: Add dev task edit/delete state and handlers**

Add refs:

```typescript
// Edit dev task modal
const showEditDevTaskModal = ref(false)
const editDevTaskId = ref('')
const editDevTaskTitle = ref('')
const editDevTaskEstimate = ref<number | null>(null)

// Delete dev task confirmation
const showDeleteDevTaskConfirm = ref(false)
const deleteDevTaskId = ref('')
const deleteDevTaskTitle = ref('')
```

Add handlers:

```typescript
function openEditDevTaskModal(task: DevTask) {
  editDevTaskId.value = task.id
  editDevTaskTitle.value = task.title
  editDevTaskEstimate.value = task.estimate_hours
  showEditDevTaskModal.value = true
}

async function handleEditDevTask() {
  if (!editDevTaskTitle.value.trim()) return
  try {
    await taskStore.updateDevTask(editDevTaskId.value, {
      title: editDevTaskTitle.value.trim(),
      estimate_hours: editDevTaskEstimate.value,
    })
    showEditDevTaskModal.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to update dev task'
  }
}

function openDeleteDevTaskConfirm(task: DevTask) {
  deleteDevTaskId.value = task.id
  deleteDevTaskTitle.value = task.title
  showDeleteDevTaskConfirm.value = true
}

async function handleDeleteDevTask() {
  try {
    await taskStore.removeDevTask(deleteDevTaskId.value)
    showDeleteDevTaskConfirm.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to delete dev task'
  }
}
```

Add `DevTask` and `TestCase` to imports:
```typescript
import type { SpecType, Priority, DevTask, TestCase } from '@/types'
```

- [ ] **Step 4: Add test case edit/delete state and handlers**

Add refs:

```typescript
// Edit test case modal
const showEditTcModal = ref(false)
const editTcId = ref('')
const editTcTitle = ref('')
const editTcPreconditions = ref('')
const editTcSteps = ref('')
const editTcExpected = ref('')
const editTcActual = ref('')

// Delete test case confirmation
const showDeleteTcConfirm = ref(false)
const deleteTcId = ref('')
const deleteTcTitle = ref('')
```

Add handlers:

```typescript
function openEditTcModal(tc: TestCase) {
  editTcId.value = tc.id
  editTcTitle.value = tc.title
  editTcPreconditions.value = tc.preconditions ?? ''
  editTcSteps.value = tc.steps
  editTcExpected.value = tc.expected_result
  editTcActual.value = tc.actual_result ?? ''
  showEditTcModal.value = true
}

async function handleEditTc() {
  if (!editTcTitle.value.trim()) return
  try {
    await tcStore.update(editTcId.value, {
      title: editTcTitle.value.trim(),
      preconditions: editTcPreconditions.value || undefined,
      steps: editTcSteps.value,
      expected_result: editTcExpected.value,
      actual_result: editTcActual.value || undefined,
    })
    showEditTcModal.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to update test case'
  }
}

function openDeleteTcConfirm(tc: TestCase) {
  deleteTcId.value = tc.id
  deleteTcTitle.value = tc.title
  showDeleteTcConfirm.value = true
}

async function handleDeleteTc() {
  try {
    await tcStore.remove(deleteTcId.value)
    showDeleteTcConfirm.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to delete test case'
  }
}
```

- [ ] **Step 5: Update template — add Edit button next to requirement title**

In the header section, after the priority badge (around line 275), add:

```html
<button
  class="text-sm text-gray-400 hover:text-gray-600 transition-colors ml-2"
  @click="openEditReqModal"
  title="Edit requirement"
>
  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
    <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
  </svg>
</button>
```

- [ ] **Step 6: Update Dev Tasks table — add Actions column**

In the Dev Tasks table, add an Actions column header and cell.

Add `<th>` after the "Created" header:

```html
<th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Actions</th>
```

Add `<td>` in each row after the "Created" cell:

```html
<td class="px-4 py-3">
  <div class="flex items-center gap-2">
    <button class="text-gray-500 hover:text-gray-700 text-xs font-semibold transition-colors" @click="openEditDevTaskModal(task)">Edit</button>
    <button v-if="task.status === 'open'" class="text-red-500 hover:text-red-700 text-xs font-semibold transition-colors" @click="openDeleteDevTaskConfirm(task)">Delete</button>
  </div>
</td>
```

- [ ] **Step 7: Update Test Tasks expanded test cases — add Edit/Delete buttons**

Replace the test case display (inside the expanded test task, around lines 487-497) with:

```html
<div v-for="tc in tcStore.testCases" :key="tc.id" class="flex items-center justify-between py-1">
  <div class="flex items-center gap-2">
    <span class="text-sm text-gray-700">{{ tc.title }}</span>
    <StatusBadge :status="tc.status" size="sm" />
  </div>
  <div class="flex items-center gap-2">
    <button class="text-gray-500 hover:text-gray-700 text-xs font-semibold transition-colors" @click="openEditTcModal(tc)">Edit</button>
    <button v-if="tc.status === 'pending'" class="text-red-500 hover:text-red-700 text-xs font-semibold transition-colors" @click="openDeleteTcConfirm(tc)">Delete</button>
  </div>
</div>
```

- [ ] **Step 8: Add all modals at end of template**

Add before the closing `</template>` (before the last `</div>`):

```html
<!-- Edit Requirement Modal -->
<Modal :show="showEditReqModal" title="Edit Requirement" @close="showEditReqModal = false">
  <div class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
      <input v-model="editReqTitle" type="text" class="input-glass" @keyup.enter="handleEditReq" />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Priority</label>
      <select v-model="editReqPriority" class="select-glass">
        <option v-for="p in (['low', 'medium', 'high', 'critical'] as Priority[])" :key="p" :value="p">{{ p.charAt(0).toUpperCase() + p.slice(1) }}</option>
      </select>
    </div>
  </div>
  <div class="flex justify-end gap-3 mt-6">
    <button class="btn-secondary" @click="showEditReqModal = false">Cancel</button>
    <button class="btn-primary" :disabled="!editReqTitle.trim()" @click="handleEditReq">Save</button>
  </div>
</Modal>

<!-- Edit Dev Task Modal -->
<Modal :show="showEditDevTaskModal" title="Edit Dev Task" @close="showEditDevTaskModal = false">
  <div class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
      <input v-model="editDevTaskTitle" type="text" class="input-glass" />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Estimate Hours</label>
      <input v-model.number="editDevTaskEstimate" type="number" min="0" class="input-glass" />
    </div>
  </div>
  <div class="flex justify-end gap-3 mt-6">
    <button class="btn-secondary" @click="showEditDevTaskModal = false">Cancel</button>
    <button class="btn-primary" :disabled="!editDevTaskTitle.trim()" @click="handleEditDevTask">Save</button>
  </div>
</Modal>

<!-- Delete Dev Task Confirmation -->
<Modal :show="showDeleteDevTaskConfirm" title="Delete Dev Task" @close="showDeleteDevTaskConfirm = false">
  <p class="text-sm text-gray-600">
    Are you sure you want to delete <span class="font-semibold text-gray-900">{{ deleteDevTaskTitle }}</span>?
  </p>
  <div class="flex justify-end gap-3 mt-6">
    <button class="btn-secondary" @click="showDeleteDevTaskConfirm = false">Cancel</button>
    <button class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors" @click="handleDeleteDevTask">Delete</button>
  </div>
</Modal>

<!-- Edit Test Case Modal -->
<Modal :show="showEditTcModal" title="Edit Test Case" @close="showEditTcModal = false">
  <div class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
      <input v-model="editTcTitle" type="text" class="input-glass" />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Preconditions</label>
      <textarea v-model="editTcPreconditions" class="input-glass resize-y" rows="2" />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Steps</label>
      <textarea v-model="editTcSteps" class="input-glass resize-y" rows="3" />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Expected Result</label>
      <textarea v-model="editTcExpected" class="input-glass resize-y" rows="2" />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Actual Result</label>
      <textarea v-model="editTcActual" class="input-glass resize-y" rows="2" />
    </div>
  </div>
  <div class="flex justify-end gap-3 mt-6">
    <button class="btn-secondary" @click="showEditTcModal = false">Cancel</button>
    <button class="btn-primary" :disabled="!editTcTitle.trim()" @click="handleEditTc">Save</button>
  </div>
</Modal>

<!-- Delete Test Case Confirmation -->
<Modal :show="showDeleteTcConfirm" title="Delete Test Case" @close="showDeleteTcConfirm = false">
  <p class="text-sm text-gray-600">
    Are you sure you want to delete <span class="font-semibold text-gray-900">{{ deleteTcTitle }}</span>?
  </p>
  <div class="flex justify-end gap-3 mt-6">
    <button class="btn-secondary" @click="showDeleteTcConfirm = false">Cancel</button>
    <button class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors" @click="handleDeleteTc">Delete</button>
  </div>
</Modal>
```

- [ ] **Step 9: Commit**

```bash
git add frontend/src/views/RequirementDetailView.vue
git commit -m "feat: add edit/delete UI for requirement, dev tasks, and test cases"
```

---

## Task 11: Frontend — Specification detail view clause edit/delete UI

**Files:**
- Modify: `frontend/src/views/SpecificationDetailView.vue`

- [ ] **Step 1: Add edit/delete clause state and handlers**

Add refs after existing modal refs (around line 29):

```typescript
// Edit clause modal (reuses add clause modal)
const isEditingClause = ref(false)
const editClauseDbId = ref('')

// Delete clause confirmation
const showDeleteClauseConfirm = ref(false)
const deleteClauseDbId = ref('')
const deleteClauseTitle = ref('')
```

- [ ] **Step 2: Add handlers**

Add after existing `handleAddClause` function:

```typescript
function openEditClauseModal(clause: SpecClause) {
  isEditingClause.value = true
  editClauseDbId.value = clause.id
  newClauseId.value = clause.clause_id
  newClauseTitle.value = clause.title
  newClauseDescription.value = clause.description
  newClauseCategory.value = clause.category
  newClauseSeverity.value = clause.severity
  showAddClauseModal.value = true
}

async function handleSaveClause() {
  if (isEditingClause.value) {
    try {
      await specStore.updateClause(editClauseDbId.value, {
        clause_id: newClauseId.value.trim(),
        title: newClauseTitle.value.trim(),
        description: newClauseDescription.value.trim(),
        category: newClauseCategory.value,
        severity: newClauseSeverity.value,
      })
      showAddClauseModal.value = false
      isEditingClause.value = false
    } catch (e: any) {
      error.value = e?.message || 'Failed to update clause'
    }
  } else {
    await handleAddClause()
  }
}

function closeClauseModal() {
  showAddClauseModal.value = false
  isEditingClause.value = false
}

function openDeleteClauseConfirm(clause: SpecClause) {
  deleteClauseDbId.value = clause.id
  deleteClauseTitle.value = clause.title
  showDeleteClauseConfirm.value = true
}

async function handleDeleteClause() {
  try {
    await specStore.removeClause(deleteClauseDbId.value)
    showDeleteClauseConfirm.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to delete clause'
  }
}
```

Import `SpecClause` type:
```typescript
import type { Severity, ClauseCategory, SpecClause } from '@/types'
```

- [ ] **Step 3: Update clause table — add Actions column**

Add `<th>` after "Description" header:

```html
<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Actions</th>
```

Replace the last `<td>` (description cell) and add Actions cell after it:

```html
<td class="px-5 py-3 text-gray-600 max-w-xs truncate">{{ clause.description }}</td>
<td class="px-5 py-3">
  <template v-if="specStore.currentVersion?.status === 'draft'">
    <div class="flex items-center gap-2">
      <button class="text-gray-500 hover:text-gray-700 text-xs font-semibold transition-colors" @click="openEditClauseModal(clause)">Edit</button>
      <button class="text-red-500 hover:text-red-700 text-xs font-semibold transition-colors" @click="openDeleteClauseConfirm(clause)">Delete</button>
    </div>
  </template>
</td>
```

- [ ] **Step 4: Update the Add Clause Modal to support dual mode**

Change the modal title to use a computed:
```html
<Modal :show="showAddClauseModal" :title="isEditingClause ? 'Edit Clause' : 'Add Clause'" @close="closeClauseModal">
```

Change the "Add Clause" button to "Save":
```html
<button class="btn-primary px-5 py-2 text-sm" :disabled="!newClauseId.trim() || !newClauseTitle.trim()" @click="handleSaveClause">{{ isEditingClause ? 'Save' : 'Add Clause' }}</button>
```

Change Cancel button:
```html
<button class="btn-secondary px-4 py-2 text-sm" @click="closeClauseModal">Cancel</button>
```

- [ ] **Step 5: Add Delete Clause Confirmation Modal**

Add before the closing `</template>`:

```html
<!-- Delete Clause Confirmation -->
<Modal :show="showDeleteClauseConfirm" title="Delete Clause" @close="showDeleteClauseConfirm = false">
  <p class="text-sm text-gray-600">
    Are you sure you want to delete clause <span class="font-semibold text-gray-900">{{ deleteClauseTitle }}</span>?
  </p>
  <div class="flex justify-end gap-3 mt-6">
    <button class="btn-secondary" @click="showDeleteClauseConfirm = false">Cancel</button>
    <button class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors" @click="handleDeleteClause">Delete</button>
  </div>
</Modal>
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/SpecificationDetailView.vue
git commit -m "feat: add edit/delete UI for spec clauses"
```

---

## Task 12: Integration verification

**Files:** None new

- [ ] **Step 1: Run backend tests**

```bash
cd backend && pytest -v
```

Expected: All tests pass (existing + new from Task 6).

- [ ] **Step 2: Run frontend build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no TypeScript errors.

- [ ] **Step 3: Start backend and verify API endpoints manually**

```bash
cd backend && uvicorn app.main:app --reload --port 8000
```

Then test:
- `PATCH /api/requirements/{id}` with `{"title": "New Title"}`
- `DELETE /api/requirements/{id}` (draft requirement)
- `PATCH /api/spec-clauses/{id}` with `{"title": "New Title"}`
- `DELETE /api/spec-clauses/{id}` (clause in draft version)
- `PATCH /api/dev-tasks/{id}` with `{"title": "New Title"}`
- `DELETE /api/dev-tasks/{id}` (open task)
- `PATCH /api/test-cases/{id}` with `{"title": "New Title"}`
- `DELETE /api/test-cases/{id}` (pending test case)

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete edit and delete functionality for requirements, clauses, tasks, and test cases"
```
