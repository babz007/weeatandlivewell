from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add category and status columns to post table
    op.add_column('post', sa.Column('category', sa.String(50)))
    op.add_column('post', sa.Column('status', sa.String(20), server_default='draft'))

def downgrade():
    # Remove the columns if we need to roll back
    op.drop_column('post', 'category')
    op.drop_column('post', 'status') 