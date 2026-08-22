"""Thin launcher for the webui Gradio app.

Usage::

    From the repository root, run ``python -m webui_launcher`` with
    ``PYTHONPATH=src`` configured.
"""

from webui.app import main


if __name__ == "__main__":
    main()
