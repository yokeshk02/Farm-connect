"""add_overlapping_booking_exclusion_constraint

Revision ID: cee83d7f2399
Revises: b063cb9dae64
Create Date: 2026-10-13 22:05:51.431113

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cee83d7f2399'
down_revision = 'b063cb9dae64'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'exclude_overlapping_confirmed_bookings'
                ) THEN
                    ALTER TABLE bookings
                    ADD CONSTRAINT exclude_overlapping_confirmed_bookings
                    EXCLUDE USING gist (
                        machinery_id WITH =,
                        tsrange(start_time, end_time, '[)') WITH &&
                    )
                    WHERE (status IN ('APPROVED', 'IN_PROGRESS'));
                END IF;
            END $$;
            """
        )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS exclude_overlapping_confirmed_bookings;")

