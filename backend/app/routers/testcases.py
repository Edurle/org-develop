from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.testcase import TestCase
from app.models.user import User
from app.schemas.testcase import TestCaseResponse, TestCaseUpdate
from app.services import testcase as testcase_svc

router = APIRouter(prefix="/api", tags=["testcases"])


class TestCaseStatusUpdate(BaseModel):
    status: str


class TestCaseCreateWithClauses(BaseModel):
    title: str
    preconditions: str | None = None
    steps: str
    expected_result: str
    clause_ids: list[str] = []


@router.post(
    "/test-tasks/{task_id}/test-cases",
    response_model=TestCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_test_case(
    task_id: str,
    body: TestCaseCreateWithClauses,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        tc = await testcase_svc.create_test_case(
            db,
            test_task_id=task_id,
            title=body.title,
            preconditions=body.preconditions,
            steps=body.steps,
            expected_result=body.expected_result,
            clause_ids=body.clause_ids,
            user_id=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return TestCaseResponse.model_validate(tc).model_dump()


@router.get(
    "/test-tasks/{task_id}/test-cases",
    response_model=list[TestCaseResponse],
)
async def list_test_cases(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(TestCase)
        .where(TestCase.test_task_id == task_id)
        .order_by(TestCase.created_at)
    )
    return [TestCaseResponse.model_validate(tc).model_dump() for tc in result.scalars().all()]


@router.patch(
    "/test-cases/{test_case_id}/status",
    response_model=TestCaseResponse,
)
async def update_test_case_status(
    test_case_id: str,
    body: TestCaseStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        tc = await testcase_svc.update_test_case_status(
            db, test_case_id=test_case_id, new_status=body.status,
            user_id=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return TestCaseResponse.model_validate(tc).model_dump()


@router.patch(
    "/test-cases/{test_case_id}",
    response_model=TestCaseResponse,
)
async def update_test_case(
    test_case_id: str,
    body: TestCaseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    update_data = body.model_dump(exclude_unset=True)
    update_data.pop("status", None)
    try:
        tc = await testcase_svc.update_test_case(
            db,
            test_case_id=test_case_id,
            user_id=user.id,
            **update_data,
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
