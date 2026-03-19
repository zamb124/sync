"""Роутеры для работы с файлами (File)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from apps.api.src.db.repositories.files import FileRepository
from apps.api.src.models.files import FileRead, FileUploadResponse


router = APIRouter()


@router.post("/", response_model=FileUploadResponse)
async def upload_file(file: UploadFile, repo: FileRepository = Depends(FileRepository)) -> FileUploadResponse:
    """Загрузка файла (MVP: сохраняем только метаданные)."""
    contents = await file.read()
    size = len(contents)
    file_id = uuid4().hex
    file_model = FileRead(
        id=file_id,
        original_name=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size,
        storage_url=f"stub://files/{file_id}",
        checksum=None,
        created_at=datetime.now(tz=UTC),
    )
    await repo.set(file_model)
    return FileUploadResponse(file=file_model)


@router.get("/{file_id}", response_model=FileRead)
async def get_file(file_id: str, repo: FileRepository = Depends(FileRepository)) -> FileRead:
    """Получение метаданных файла."""
    f = await repo.get(file_id)
    if f is None:
        raise HTTPException(status_code=404, detail="Файл не найден.")
    return f

