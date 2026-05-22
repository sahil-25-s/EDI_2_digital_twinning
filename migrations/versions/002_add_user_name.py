"""Add user name column

Revision ID: 002_add_user_name
Revises: 001_initial
"""
import sqlalchemy as sa
from alembic import op

revision = "002_add_user_name"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "name" in columns:
        return
    op.add_column("users", sa.Column("name", sa.String(length=120), nullable=True))
    op.execute(sa.text("UPDATE users SET name = email WHERE name IS NULL"))
    op.alter_column("users", "name", nullable=False)


def downgrade():
    op.drop_column("users", "name")
