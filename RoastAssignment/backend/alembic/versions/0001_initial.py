"""Initial schema: users, refresh_tokens, submissions, evaluations.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role_enum = sa.Enum("student", "examiner", "coach", name="userrole")
sync_status_enum = sa.Enum("pending", "synced", "error", name="syncstatus")
evaluation_status_enum = sa.Enum(
    "pending", "running", "completed", "failed", name="evaluationstatus"
)


def upgrade() -> None:
    # --- users ---------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=100), nullable=True),
        sa.Column(
            "role",
            user_role_enum,
            nullable=False,
            server_default="student",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column("oauth_provider", sa.String(length=50), nullable=True),
        sa.Column("google_id", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)

    # --- refresh_tokens --------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=500), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        op.f("ix_refresh_tokens_id"), "refresh_tokens", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_refresh_tokens_token"), "refresh_tokens", ["token"], unique=True
    )

    # --- submissions -----------------------------------------------------
    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("student_name", sa.String(length=200), nullable=False),
        sa.Column("student_email", sa.String(length=255), nullable=False),
        sa.Column("assignment_name", sa.String(length=200), nullable=False),
        sa.Column("github_repo_url", sa.String(length=500), nullable=False),
        sa.Column(
            "google_form_response_id", sa.String(length=255), nullable=False
        ),
        sa.Column(
            "sync_status",
            sync_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("google_form_response_id"),
    )
    op.create_index(op.f("ix_submissions_id"), "submissions", ["id"], unique=False)
    op.create_index(
        op.f("ix_submissions_user_id"), "submissions", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_submissions_student_email"),
        "submissions",
        ["student_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_submissions_google_form_response_id"),
        "submissions",
        ["google_form_response_id"],
        unique=True,
    )
    op.create_index(
        "ix_submissions_user_submitted",
        "submissions",
        ["user_id", "submitted_at"],
        unique=False,
    )

    # --- evaluations -------------------------------------------------------
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("ai_roast_text", sa.Text(), nullable=True),
        sa.Column("ai_score", sa.Float(), nullable=True),
        sa.Column("static_analysis_report", sa.JSON(), nullable=True),
        sa.Column("static_analysis_score", sa.Float(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column(
            "status",
            evaluation_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["submission_id"], ["submissions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("submission_id"),
    )
    op.create_index(op.f("ix_evaluations_id"), "evaluations", ["id"], unique=False)
    op.create_index(
        op.f("ix_evaluations_submission_id"),
        "evaluations",
        ["submission_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluations_submission_id"), table_name="evaluations")
    op.drop_index(op.f("ix_evaluations_id"), table_name="evaluations")
    op.drop_table("evaluations")

    op.drop_index("ix_submissions_user_submitted", table_name="submissions")
    op.drop_index(
        op.f("ix_submissions_google_form_response_id"), table_name="submissions"
    )
    op.drop_index(op.f("ix_submissions_student_email"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_user_id"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_id"), table_name="submissions")
    op.drop_table("submissions")

    op.drop_index(op.f("ix_refresh_tokens_token"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")

    evaluation_status_enum.drop(op.get_bind(), checkfirst=True)
    sync_status_enum.drop(op.get_bind(), checkfirst=True)
    user_role_enum.drop(op.get_bind(), checkfirst=True)
