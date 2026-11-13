import subprocess
import sys

print("Installing requirements...")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

print("Installing Playwright browsers...")
subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)

from pathlib import Path

project_root = Path(__file__).resolve().parent
launcher = project_root / "bin" / "Jarvis"
local_bin = Path.home() / ".local" / "bin"
local_bin.mkdir(parents=True, exist_ok=True)
target = local_bin / "Jarvis"
target.unlink(missing_ok=True)
target.symlink_to(launcher)

print("\n✅ Setup complete! Run 'Jarvis' to start Jarvis.")
