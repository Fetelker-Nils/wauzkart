"""Wauz Kart game package."""

__version__ = "1.0.37"

def main():
    from .app import main as run_main

    return run_main()


def __getattr__(name):
    if name == "MainWindow":
        from .ui.main_window import MainWindow

        return MainWindow
    raise AttributeError(name)

__all__ = ["MainWindow", "main", "__version__"]
