"""initial migration

Revision ID: 202511101800_29ea10
Revises: 
Create Date: 2025-11-10 18:00:10 UTC
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "202511101800_29ea10"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tip: replace with real tables or regenerate via:
    #   alembic revision --autogenerate -m "initial"
    # and delete this file.
    pass


def downgrade() -> None:
    # Tip: implement opposite of upgrade() if you customized it.
    pass
