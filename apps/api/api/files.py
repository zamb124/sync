"""Роутеры для работы с файлами (File)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, UploadFile

from apps.api.src.models.files import FileRead, FileUploadResponse


router = APIRouter()


@router.post("/", response_model=FileUploadResponse)
async def upload_file(file: UploadFile) -> FileUploadResponse:
    """Загрузка файла (заглушка, без фактического сохранения)."""
    contents = await file.read()
    size = len(contents)
    file_model = FileRead(
        id="file-example",
        original_name=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size,
        storage_url="s3://example-bucket/file-example",
        checksum=None,
        created_at=datetime.utcnow(),
    )
    return FileUploadResponse(file=file_model)


@router.get("/{file_id}", response_model=FileRead)
async def get_file(file_id: str) -> FileRead:
    """Получение метаданных файла (заглушка)."""
    return FileRead(
        id=file_id,
        original_name="example.txt",
        mime_type="text/plain",
        size_bytes=0,
        storage_url="s3://example-bucket/file-example",
        checksum=None,
        created_at=datetime.utcnow(),
    )

