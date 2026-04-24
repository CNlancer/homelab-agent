from pathlib import Path

from homelab_agent.config.loader import load_target_config


def test_load_target_config_reads_local_secret_profile(tmp_path: Path):
    secrets_dir = tmp_path / "local" / "secrets"
    secrets_dir.mkdir(parents=True)
    profile_path = secrets_dir / "unraid-tower.json"
    profile_path.write_text(
        """
        {
          "label": "unraid-tower",
          "base_url": "http://10.0.0.11/",
          "ssh_host": "10.0.0.11",
          "ssh_username": "root",
          "ssh_password": "secret"
        }
        """.strip()
    )

    config = load_target_config("unraid-tower", config_root=tmp_path / "local" / "secrets")

    assert config.label == "unraid-tower"
    assert config.ssh_host == "10.0.0.11"
    assert config.ssh_username == "root"
    assert config.ssh_password == "secret"
