"""HTTP endpoints for projects and their backlog. Planning and building happen in workers;
each call here returns at once."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.features.projects.dependencies import get_backlog_progress, get_project_service
from app.features.projects.progress import BacklogProgress
from app.features.projects.schemas import (
    BacklogItem,
    ItemFields,
    ItemUpdate,
    NewProject,
    Project,
    ProjectDetail,
    ProjectUpdate,
)
from app.features.projects.service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])
Service = Annotated[ProjectService, Depends(get_project_service)]
Progress = Annotated[BacklogProgress, Depends(get_backlog_progress)]


@router.post("", response_model=ProjectDetail, status_code=status.HTTP_202_ACCEPTED)
async def create_project(body: NewProject, service: Service) -> ProjectDetail:
    """Create the project; the PM starts planning its backlog."""
    return await service.create(body)


@router.get("", response_model=list[Project])
async def list_projects(
    service: Service, limit: Annotated[int, Query(ge=1, le=200)] = 50
) -> list[Project]:
    return await service.list(limit)


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str, service: Service) -> ProjectDetail:
    return await service.get(project_id)


@router.patch("/{project_id}", response_model=ProjectDetail)
async def update_project(project_id: str, body: ProjectUpdate, service: Service) -> ProjectDetail:
    return await service.update(project_id, body)


@router.post("/{project_id}/plan", response_model=ProjectDetail, status_code=202)
async def replan(project_id: str, service: Service) -> ProjectDetail:
    """Ask the PM again: items not started yet are replaced by a new proposal."""
    return await service.replan(project_id)


@router.post("/{project_id}/plan/approve", response_model=ProjectDetail)
async def approve_plan(project_id: str, service: Service) -> ProjectDetail:
    return await service.approve_plan(project_id)


@router.post("/{project_id}/pause", response_model=ProjectDetail)
async def pause(project_id: str, service: Service) -> ProjectDetail:
    return await service.pause(project_id)


@router.post("/{project_id}/resume", response_model=ProjectDetail)
async def resume(project_id: str, service: Service) -> ProjectDetail:
    return await service.resume(project_id)


@router.post("/{project_id}/next", response_model=BacklogItem, status_code=202)
async def start_next(project_id: str, progress: Progress) -> BacklogItem:
    """Start the next to-do item now (outside autopilot, or beyond today's limit)."""
    return await progress.start_next(project_id)


@router.post("/{project_id}/items", response_model=BacklogItem, status_code=201)
async def add_item(project_id: str, body: ItemFields, service: Service) -> BacklogItem:
    return await service.add_item(project_id, body)


@router.patch("/{project_id}/items/{item_id}", response_model=BacklogItem)
async def update_item(
    project_id: str, item_id: str, body: ItemUpdate, service: Service
) -> BacklogItem:
    return await service.update_item(project_id, item_id, body)


@router.delete("/{project_id}/items/{item_id}", status_code=204)
async def delete_item(project_id: str, item_id: str, service: Service) -> Response:
    await service.delete_item(project_id, item_id)
    return Response(status_code=204)


@router.post("/{project_id}/items/{item_id}/skip", response_model=BacklogItem)
async def skip_item(project_id: str, item_id: str, service: Service) -> BacklogItem:
    return await service.skip_item(project_id, item_id)


@router.post("/{project_id}/items/{item_id}/retry", response_model=BacklogItem)
async def retry_item(project_id: str, item_id: str, service: Service) -> BacklogItem:
    return await service.retry_item(project_id, item_id)
