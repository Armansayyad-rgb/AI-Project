"""Gradio web UI for the AI Project RAG chatbot.

This package wraps the CLI pipeline in ``rag_chat_v2`` so non-technical
users can interact with the same model through a browser. The pipeline
itself is not modified; the UI re-runs the retrievers separately to
collect source chunks for display.
"""

__all__ = ["app", "chat_handler", "ui_components"]
