"""initial SaaS workspace schema

Revision ID: 0001_initial_saas_workspace
Revises:
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_saas_workspace"
down_revision = None
branch_labels = None
depends_on = None


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def uuid_pk() -> sa.Column:
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)


def upgrade() -> None:
    op.create_table(
        "users",
        uuid_pk(),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("auth_provider", sa.String(length=80), nullable=False),
        sa.Column("billing_customer_id", sa.String(length=255), nullable=True),
        *timestamp_columns(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_unique_constraint("uq_users_billing_customer_id", "users", ["billing_customer_id"])

    op.create_table(
        "subscription_plans",
        uuid_pk(),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("billing_provider_price_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("ix_subscription_plans_code", "subscription_plans", ["code"], unique=True)
    op.create_index("ix_subscription_plans_status", "subscription_plans", ["status"])

    op.create_table(
        "user_subscriptions",
        uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_plans.id"), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("billing_provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
    )
    op.create_index("ix_user_subscriptions_user_id", "user_subscriptions", ["user_id"])
    op.create_index("ix_user_subscriptions_status", "user_subscriptions", ["status"])
    op.create_unique_constraint(
        "uq_user_subscriptions_billing_provider_subscription_id",
        "user_subscriptions",
        ["billing_provider_subscription_id"],
    )

    op.create_table(
        "resumes",
        uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("parser_version", sa.String(length=50), nullable=True),
        sa.Column("processing_state", sa.String(length=30), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])
    op.create_index("ix_resumes_processing_state", "resumes", ["processing_state"])

    op.create_table(
        "resume_blocks",
        uuid_pk(),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("section_type", sa.String(length=100), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("layout_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("ix_resume_blocks_resume_id", "resume_blocks", ["resume_id"])

    op.create_table(
        "candidate_profiles",
        uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("profile_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("ix_candidate_profiles_user_id", "candidate_profiles", ["user_id"])
    op.create_unique_constraint("uq_candidate_profiles_resume_id", "candidate_profiles", ["resume_id"])

    op.create_table(
        "verified_facts",
        uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("source_block_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resume_blocks.id"), nullable=True),
        sa.Column("fact_type", sa.String(length=100), nullable=False),
        sa.Column("section", sa.String(length=100), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("verified_by_user", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("ix_verified_facts_user_id", "verified_facts", ["user_id"])
    op.create_index("ix_verified_facts_resume_id", "verified_facts", ["resume_id"])

    op.create_table(
        "resume_versions",
        uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("base_resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("version_name", sa.String(length=200), nullable=False),
        sa.Column("target_role", sa.String(length=200), nullable=True),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("change_log_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("ix_resume_versions_user_id", "resume_versions", ["user_id"])

    op.create_table(
        "jobs",
        uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("company", sa.String(length=200), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("raw_description", sa.Text(), nullable=False),
        sa.Column("parsed_job_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("processing_state", sa.String(length=30), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
    op.create_index("ix_jobs_processing_state", "jobs", ["processing_state"])

    op.create_table(
        "analyses",
        uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=True),
        sa.Column("preferred_language", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("candidate_name", sa.String(length=255), nullable=True),
        sa.Column("top_direction", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("analysis_job_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("career_directions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("suggestions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *timestamp_columns(),
    )
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"])
    op.create_index("ix_analyses_resume_id", "analyses", ["resume_id"])
    op.create_index("ix_analyses_status", "analyses", ["status"])

    op.create_table(
        "matches",
        uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=True),
        sa.Column("component_scores_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("explanation_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("ix_matches_user_id", "matches", ["user_id"])
    op.create_index("ix_matches_resume_id", "matches", ["resume_id"])
    op.create_index("ix_matches_job_id", "matches", ["job_id"])

    op.create_table(
        "suggestions",
        uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id"), nullable=True),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("section", sa.String(length=100), nullable=False),
        sa.Column("item_index", sa.Integer(), nullable=False),
        sa.Column("item_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("suggested_text", sa.Text(), nullable=True),
        sa.Column("edited_text", sa.Text(), nullable=True),
        sa.Column("source_fact_ids", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("risk_level", sa.String(length=30), nullable=False),
        sa.Column("requires_user_confirmation", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("ix_suggestions_user_id", "suggestions", ["user_id"])
    op.create_index("ix_suggestions_analysis_id", "suggestions", ["analysis_id"])
    op.create_index("ix_suggestions_resume_id", "suggestions", ["resume_id"])
    op.create_index("ix_suggestions_job_id", "suggestions", ["job_id"])
    op.create_index("ix_suggestions_status", "suggestions", ["status"])

    op.create_table(
        "agent_runs",
        uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("run_type", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("trace_id", sa.String(length=200), nullable=True),
        sa.Column("token_usage", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        *timestamp_columns(),
    )
    op.create_index("ix_agent_runs_user_id", "agent_runs", ["user_id"])
    op.create_index("ix_agent_runs_run_type", "agent_runs", ["run_type"])
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])
    op.create_index("ix_agent_runs_trace_id", "agent_runs", ["trace_id"])


def downgrade() -> None:
    for table in [
        "agent_runs",
        "suggestions",
        "matches",
        "analyses",
        "jobs",
        "resume_versions",
        "verified_facts",
        "candidate_profiles",
        "resume_blocks",
        "resumes",
        "user_subscriptions",
        "subscription_plans",
        "users",
    ]:
        op.drop_table(table)
