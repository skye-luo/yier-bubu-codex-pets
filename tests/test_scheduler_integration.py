"""Run the real scheduler against an isolated home, never the live app."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SchedulerIntegrationTests(unittest.TestCase):
    def test_all_task_and_time_combinations_preserve_point_and_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder) / ".codex"
            assets = home / "pet-sleep-mode" / "assets"
            assets.mkdir(parents=True)
            config = '[desktop]\nselected-avatar-id = "custom:bubu"\n'
            (home / "config.toml").write_text(config, encoding="utf-8")
            for pet in ("yier", "bubu", "dianzai"):
                (home / "pets" / pet).mkdir(parents=True)
                for mode in ("awake", "sleep"):
                    (assets / f"{pet}-{mode}.webp").write_bytes(f"{pet}:{mode}".encode())
                    if pet != "dianzai":
                        for kind in ("research", "writing"):
                            (assets / f"{pet}-{kind}-{mode}.webp").write_bytes(f"{pet}:{kind}:{mode}".encode())
            env = dict(os.environ, CODEX_PET_NODE=str(home / "no-live-app"))
            for mode in ("awake", "sleep"):
                for kind in ("coding", "research", "writing"):
                    command = [sys.executable, str(ROOT / "scripts/pet_sleep_scheduler.py"),
                               "--codex-root", str(home), "--mode", mode, "--activity", kind]
                    subprocess.run(command, check=True, env=env, capture_output=True)
                    for pet in ("yier", "bubu", "dianzai"):
                        suffix = f"{kind}:{mode}" if pet != "dianzai" and kind != "coding" else mode
                        self.assertEqual((home / "pets" / pet / "spritesheet.webp").read_bytes(), f"{pet}:{suffix}".encode())
                    state = json.loads((home / "pet-sleep-mode/state.json").read_text())
                    self.assertEqual((state["last_mode"], state["last_activity"]), (mode, kind))
                    self.assertEqual((home / "config.toml").read_text(), config)
            before = (home / "pets/bubu/spritesheet.webp").read_bytes()
            subprocess.run(command[:-4] + ["--mode", "awake", "--activity", "coding", "--dry-run"],
                           check=True, env=env, capture_output=True)
            self.assertEqual((home / "pets/bubu/spritesheet.webp").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
