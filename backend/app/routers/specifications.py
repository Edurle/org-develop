from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.specification import Specification, SpecVersion
from app.models.user import User
from app.schemas.specification import (
    SpecificationCreate,
    SpecificationResponse,
    SpecVersionCreate,
    SpecVersionResponse,
    SpecClauseCreate,
    SpecClauseUpdate,
    SpecClauseResponse,
)
from app.services import specification as specification_svc
from app.services import clause as clause_svc
from app.services.audit import log_action

router = APIRouter(prefix="/api", tags=["specifications"])


# ---------------------------------------------------------------------------
# Specifications
# ---------------------------------------------------------------------------


@router.post(
    "/requirements/{requirement_id}/specifications",
    response_model=SpecificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_specification(
    requirement_id: str,
    body: SpecificationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        spec = await specification_svc.create_specification(
            db,
            requirement_id=requirement_id,
            spec_type=body.spec_type,
            title=body.title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="specification.create",
        resource_type="specification", resource_id=spec.id,
        detail=f"Created {body.spec_type} specification '{body.title}'",
    )
    return SpecificationResponse.model_validate(spec).model_dump()


@router.get(
    "/requirements/{requirement_id}/specifications",
    response_model=list[SpecificationResponse],
)
async def list_specifications(
    requirement_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Specification)
        .where(Specification.requirement_id == requirement_id)
        .order_by(Specification.created_at)
    )
    return [SpecificationResponse.model_validate(s).model_dump() for s in result.scalars().all()]


# ---------------------------------------------------------------------------
# Spec Versions
# ---------------------------------------------------------------------------


@router.post(
    "/specifications/{spec_id}/versions",
    response_model=SpecVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_spec_version(
    spec_id: str,
    body: SpecVersionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        version = await specification_svc.create_spec_version(
            db, spec_id=spec_id, content=body.content
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="specification.create_version",
        resource_type="spec_version", resource_id=version.id,
        detail=f"Created spec version v{version.version}",
    )
    return SpecVersionResponse.model_validate(version).model_dump()


@router.get(
    "/specifications/{spec_id}/versions",
    response_model=list[SpecVersionResponse],
)
async def list_spec_versions(
    spec_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(SpecVersion)
        .where(SpecVersion.spec_id == spec_id)
        .order_by(SpecVersion.version)
    )
    return [SpecVersionResponse.model_validate(v).model_dump() for v in result.scalars().all()]


@router.patch("/spec-versions/{version_id}/submit", response_model=SpecVersionResponse)
async def submit_spec_version(
    version_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    try:
        version = await specification_svc.submit_spec_for_review(db, version_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return SpecVersionResponse.model_validate(version).model_dump()


@router.patch("/spec-versions/{version_id}/lock", response_model=SpecVersionResponse)
async def lock_spec_version(
    version_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        version = await specification_svc.lock_spec(db, version_id, user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return SpecVersionResponse.model_validate(version).model_dump()


@router.patch("/spec-versions/{version_id}/reject", response_model=SpecVersionResponse)
async def reject_spec_version(
    version_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        version = await specification_svc.reject_spec(db, version_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="specification.reject",
        resource_type="spec_version", resource_id=version.id,
        detail=f"Rejected spec version v{version.version}",
    )
    return SpecVersionResponse.model_validate(version).model_dump()


# ---------------------------------------------------------------------------
# Spec Clauses
# ---------------------------------------------------------------------------


@router.post(
    "/spec-versions/{version_id}/clauses",
    response_model=SpecClauseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_clause(
    version_id: str,
    body: SpecClauseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        clause = await clause_svc.create_clause(
            db,
            spec_version_id=version_id,
            clause_id=body.clause_id,
            title=body.title,
            description=body.description,
            category=body.category,
            severity=body.severity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="clause.create",
        resource_type="spec_clause", resource_id=clause.id,
        detail=f"Created clause '{body.clause_id}' ({body.severity})",
    )
    return SpecClauseResponse.model_validate(clause).model_dump()


@router.get(
    "/spec-versions/{version_id}/clauses",
    response_model=list[SpecClauseResponse],
)
async def list_clauses(
    version_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    clauses = await clause_svc.list_clauses(db, spec_version_id=version_id)
    return [SpecClauseResponse.model_validate(c).model_dump() for c in clauses]


@router.patch("/spec-clauses/{clause_id}", response_model=SpecClauseResponse)
async def update_clause(
    clause_id: str,
    body: SpecClauseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        clause = await clause_svc.update_clause(
            db,
            clause_id=clause_id,
            clause_id_str=body.clause_id,
            title=body.title,
            description=body.description,
            category=body.category,
            severity=body.severity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="clause.update",
        resource_type="spec_clause", resource_id=clause.id,
        detail=f"Updated clause '{clause.clause_id}'",
    )
    return SpecClauseResponse.model_validate(clause).model_dump()


@router.delete("/spec-clauses/{clause_id}", status_code=status.HTTP_204_NO_CONTENT)
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
