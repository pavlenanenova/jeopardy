"""create questions table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("show_number", sa.Integer, nullable=False),
        sa.Column("air_date", sa.Date, nullable=False),
        sa.Column("round", sa.String, nullable=False),
        sa.Column("category", sa.String, nullable=False),
        sa.Column("value", sa.String, nullable=True),
        sa.Column("question", sa.String, nullable=False),
        sa.Column("answer", sa.String, nullable=False),
        sa.UniqueConstraint("show_number", "question", name="uq_show_question"),
    )
    op.create_index("ix_questions_round_value", "questions", ["round", "value"])


def downgrade() -> None:
    op.drop_index("ix_questions_round_value", table_name="questions")
    op.drop_table("questions")