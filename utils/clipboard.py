from config import CLIPBOARD_CLEAR_SECONDS

_clear_job = None


def copy_with_auto_clear(root, text: str) -> None:
    global _clear_job

    root.clipboard_clear()
    root.clipboard_append(text)

    if _clear_job is not None:
        root.after_cancel(_clear_job)

    _clear_job = root.after(
        CLIPBOARD_CLEAR_SECONDS * 1000,
        lambda: _do_clear(root),
    )


def _do_clear(root) -> None:
    global _clear_job
    try:
        root.clipboard_clear()
    except Exception:
        pass
    _clear_job = None
