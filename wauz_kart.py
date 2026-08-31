import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


if __name__ == "__main__":
    if "--smoke-import" in sys.argv:
        import importlib.util

        if importlib.util.find_spec("wauzkart.ui.main_window") is None:
            raise ModuleNotFoundError("No module named 'wauzkart.ui.main_window'")

        sys.exit(0)
    from wauzkart.app import main

    main()
