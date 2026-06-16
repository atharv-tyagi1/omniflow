"""phase_15_telegram_uniqueness

Revision ID: 0g9l3n04m2e68
Revises: 0f866a056e47
Create Date: 2026-06-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0g9l3n04m2e68'
down_revision: Union[str, Sequence[str], None] = '0f866a056e47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_workspace_customer_telegram_id', ['workspace_id', 'telegram_id'])


def downgrade() -> None:
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.drop_constraint('uq_workspace_customer_telegram_id', type_='unique')
