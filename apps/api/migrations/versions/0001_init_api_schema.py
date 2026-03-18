from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_init_api_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "spaces",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=64), nullable=False),
    )

    op.create_table(
        "channels",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("space_id", sa.String(length=64), nullable=True),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("is_private", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["space_id"], ["spaces.id"]),
    )

    op.create_table(
        "channel_members",
        sa.Column("channel_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("channel_id", "user_id"),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "threads",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("channel_id", sa.String(length=64), nullable=False),
        sa.Column("root_message_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "files",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_url", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "git_resource_refs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("project_key", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("extra", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("channel_id", sa.String(length=64), nullable=False),
        sa.Column("thread_id", sa.String(length=64), nullable=True),
        sa.Column("parent_message_id", sa.String(length=64), nullable=True),
        sa.Column("sender_user_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thread_id"], ["threads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_message_id"], ["messages.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "message_contents",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "message_files",
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column("file_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("message_id", "file_id"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("message_files")
    op.drop_table("message_contents")
    op.drop_table("messages")
    op.drop_table("git_resource_refs")
    op.drop_table("files")
    op.drop_table("threads")
    op.drop_table("channel_members")
    op.drop_table("channels")
    op.drop_table("spaces")

