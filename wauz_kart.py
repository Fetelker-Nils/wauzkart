import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


if __name__ == "__main__":
    if "--smoke-import" in sys.argv:
        import wauzkart.ui.main_window  # noqa: F401

        sys.exit(0)
    from wauzkart.app import main

    main()
