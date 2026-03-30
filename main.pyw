import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from gui.app import PasswordVaultApp

if __name__ == "__main__":
    app = PasswordVaultApp()
    app.mainloop()
