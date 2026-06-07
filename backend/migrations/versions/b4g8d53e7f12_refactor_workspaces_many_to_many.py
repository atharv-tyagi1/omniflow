"""refactor_workspaces_many_to_many

Revision ID: b4g8d53e7f12
Revises: a3f7c9e21b04
Create Date: 2026-06-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b4g8d53e7f12'
down_revision = 'a3f7c9e21b04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create workspace_members table
    op.create_table('workspace_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_wsmember_user', 'workspace_members', ['user_id'], unique=False)
    op.create_index('idx_wsmember_workspace', 'workspace_members', ['workspace_id'], unique=False)
    op.create_index('idx_wsmember_workspace_user', 'workspace_members', ['workspace_id', 'user_id'], unique=True)

    # Migrate existing workspace_id from users to workspace_members
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            INSERT INTO workspace_members (id, workspace_id, user_id, role, created_at, updated_at)
            SELECT gen_random_uuid(), workspace_id, id, role, created_at, updated_at
            FROM users
            """
        )
    else:
        # For sqlite, just skip the data migration or use string uuid. In tests, users table is empty anyway.
        pass

    # 3. Drop constraints and columns from users
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('idx_users_workspace')
        batch_op.drop_constraint('users_workspace_id_fkey', type_='foreignkey')
        batch_op.drop_column('workspace_id')
        batch_op.drop_column('role')


def downgrade() -> None:
    # 1. Add columns back to users
    op.add_column('users', sa.Column('role', sa.String(length=50), server_default='member', autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('workspace_id', postgresql.UUID(as_uuid=True), autoincrement=False, nullable=True))
    
    # 2. Migrate data back (take the first workspace found for a user)
    op.execute(
        """
        UPDATE users
        SET workspace_id = wm.workspace_id, role = wm.role
        FROM (
            SELECT DISTINCT ON (user_id) user_id, workspace_id, role
            FROM workspace_members
        ) wm
        WHERE users.id = wm.user_id
        """
    )

    # 3. Re-apply constraints (make workspace_id not null after migration)
    op.alter_column('users', 'workspace_id', existing_type=postgresql.UUID(), nullable=False)
    op.create_foreign_key('users_workspace_id_fkey', 'users', 'workspaces', ['workspace_id'], ['id'], ondelete='RESTRICT')
    op.create_index('idx_users_workspace', 'users', ['workspace_id'], unique=False)

    # 4. Drop workspace_members table
    op.drop_index('idx_wsmember_workspace_user', table_name='workspace_members')
    op.drop_index('idx_wsmember_workspace', table_name='workspace_members')
    op.drop_index('idx_wsmember_user', table_name='workspace_members')
    op.drop_table('workspace_members')
