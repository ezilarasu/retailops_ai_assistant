import logging
import sys

# Libraries that log every HTTP request or model-file lookup at INFO. Left alone they
# bury the app's own log lines (route_selected, rag_stage_timing, retrieved_doc, ...).
# groq is not listed: its "Retrying request ... in N seconds" lines show rate limiting.
NOISY_LOGGERS = (
    "httpx",
    "httpcore",
    "sentence_transformers",
    "huggingface_hub",
    "urllib3",
    "filelock",
)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
    )

    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    # Hide the "Loading weights" progress bars printed while models load.
    try:
        from huggingface_hub.utils import disable_progress_bars

        disable_progress_bars()
    except ImportError:
        pass

    try:
        from transformers.utils import logging as transformers_logging

        transformers_logging.disable_progress_bar()
    except ImportError:
        pass
