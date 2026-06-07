"""cc lineage fields

Revision ID: g9l3n04m2e67
Revises: f8k2l93m1d56
Create Date: 2026-06-06 17:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'g9l3n04m2e67'
down_revision = 'f8k2l93m1d56'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('customer_care_cases', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_case_id', postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.create_foreign_key('fk_cc_parent_case_id', 'customer_care_cases', ['parent_case_id'], ['id'], ondelete='SET NULL')
        batch_op.add_column(sa.Column('handoff_reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('handoff_stage', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('source_channel', sa.String(length=50), nullable=True))

def downgrade() -> None:
    with op.batch_alter_table('customer_care_cases', schema=None) as batch_op:
        batch_op.drop_constraint('fk_cc_parent_case_id', type_='foreignkey')
        batch_op.drop_column('source_channel')
        batch_op.drop_column('handoff_stage')
        batch_op.drop_column('handoff_reason')
        batch_op.drop_column('parent_case_id')
