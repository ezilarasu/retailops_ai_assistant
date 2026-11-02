import time


def record_timing(
    state: dict,
    stage: str,
    start_time: float,
):
    timings = state.get(
        "timings",
        {},
    )

    timings[stage] = round(
        (time.perf_counter() - start_time)
        * 1000,
        2,
    )

    return timings

def history_before_question(state: dict) -> list:
    """Earlier turns only. route_node has already appended the current question
    to state["messages"], so the last message is the question being answered."""
    return state.get("messages", [])[:-1]


def add_total_timing(state: dict, timings: dict) -> dict:
    workflow_start = state.get("_workflow_start")

    if workflow_start is not None:
        timings["total_ms"] = round(
            (time.perf_counter() - workflow_start) * 1000,
            2,
        )

    return timings