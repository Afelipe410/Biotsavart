from __future__ import annotations
import sys
from PyQt6.QtWidgets import QApplication


def main() -> int:
    app = QApplication(sys.argv)
    from .ui import MainWindow
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
