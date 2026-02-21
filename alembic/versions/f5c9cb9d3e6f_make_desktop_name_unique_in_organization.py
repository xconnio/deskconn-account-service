"""make desktop name unique in organization

Revision ID: f5c9cb9d3e6f
Revises: 49e1c139f5fc
Create Date: 2026-02-21 15:09:18.550212

"""

from typing import Sequence, Union

from alembic import op


revision: str = "f5c9cb9d3e6f"
down_revision: Union[str, Sequence[str], None] = "49e1c139f5fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("desktops", schema=None) as batch_op:
        batch_op.alter_column("name", nullable=False)
        batch_op.create_unique_constraint("uq_desktop_org_name", ["organization_id", "name"])


def downgrade() -> None:
    with op.batch_alter_table("desktops", schema=None) as batch_op:
        batch_op.drop_constraint("uq_desktop_org_name", type_="unique")
        batch_op.alter_column("name", nullable=True)
