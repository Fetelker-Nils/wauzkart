import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(APP_DIR / "src"))


if __name__ == "__main__":
    if "--smoke-import" in sys.argv:
        from wauzkart.app import MainWindow  # noqa: F401
        from wauzkart.ui.main_window import MainWindow as UiMainWindow  # noqa: F401

        sys.exit(0)
    from wauzkart.app import main

    main()
