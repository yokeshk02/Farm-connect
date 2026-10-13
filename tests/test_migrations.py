import os
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_configuration_and_migration_scripts():
    """Verify that Alembic configuration and migration versions are valid."""
    base_dir = Path(__file__).resolve().parent.parent
    alembic_ini_path = base_dir / "migrations" / "alembic.ini"
    assert alembic_ini_path.exists(), "migrations/alembic.ini must exist"

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(base_dir / "migrations"))

    script = ScriptDirectory.from_config(alembic_cfg)
    heads = script.get_heads()
    assert len(heads) == 1, f"Expected single migration head, found: {heads}"
    assert heads[0] == "aeacc557d85c"
