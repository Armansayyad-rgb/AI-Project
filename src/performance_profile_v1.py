import time
from statistics import mean

from rag_chat_v2 import (
    initialize_pipeline,
    answer_question,
)


# --------------------------------------------------
# Profiling questions
# --------------------------------------------------

PROFILE_CASES = [
    {
        "name": "extractor",
        "question": "When was Albert Einstein born?",
    },
    {
        "name": "causal",
        "question": "Why did the Roman Empire decline?",
    },
    {
        "name": "change",
        "question": "How did the Roman Empire change over time?",
    },
    {
        "name": "structure",
        "question": "Explain the structure of DNA.",
    },
    {
        "name": "summary",
        "question": "Explain how photosynthesis works.",
    },
    {
        "name": "comparison",
        "question": "What are the differences between mitosis and meiosis?",
    },
    {
        "name": "false_relation",
        "question": "How did DNA lead to the Roman Empire?",
    },
]


# --------------------------------------------------
# Utility
# --------------------------------------------------

def timed_call(
    pipeline,
    question,
):
    start = time.perf_counter()

    result = answer_question(
        pipeline,
        question,
        verbose=False,
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    return result, elapsed


def format_seconds(value):
    return f"{value:.3f}s"


# --------------------------------------------------
# Repeated profiling
# --------------------------------------------------

def profile_case(
    pipeline,
    case,
    runs=3,
):
    timings = []

    results = []

    for run_index in range(
        runs
    ):
        result, elapsed = timed_call(
            pipeline,
            case[
                "question"
            ],
        )

        timings.append(
            elapsed
        )

        results.append(
            result
        )

    latest = results[-1]

    return {
        "name":
            case[
                "name"
            ],

        "question":
            case[
                "question"
            ],

        "timings":
            timings,

        "average":
            mean(
                timings
            ),

        "minimum":
            min(
                timings
            ),

        "maximum":
            max(
                timings
            ),

        "router":
            latest.get(
                "router"
            ),

        "retriever":
            latest.get(
                "retriever"
            ),

        "answer_type":
            latest.get(
                "answer_type"
            ),

        "supported":
            latest.get(
                "supported"
            ),

        "retrieval_score":
            latest.get(
                "retrieval_score"
            ),

        "reasoning_support":
            latest.get(
                "reasoning_support"
            ),

        "comparison_confidence":
            latest.get(
                "comparison_confidence"
            ),
    }


# --------------------------------------------------
# Comparison-specific inspection
# --------------------------------------------------

def print_comparison_details(
    result,
):
    confidence = result.get(
        "comparison_confidence"
    )

    if not confidence:
        return

    print(
        "Comparison confidence:"
    )

    left = confidence.get(
        "left",
        {},
    )

    right = confidence.get(
        "right",
        {},
    )

    print(
        "  Left score:",
        left.get(
            "score"
        ),
    )

    print(
        "  Right score:",
        right.get(
            "score"
        ),
    )

    print(
        "  Sufficient:",
        confidence.get(
            "sufficient"
        ),
    )


# --------------------------------------------------
# Reasoning support inspection
# --------------------------------------------------

def print_reasoning_support(
    result,
):
    support = result.get(
        "reasoning_support"
    )

    if not support:
        return

    print(
        "Reasoning support:"
    )

    print(
        "  Score:",
        support.get(
            "score"
        ),
    )

    print(
        "  Coverage:",
        support.get(
            "term_coverage"
        ),
    )

    print(
        "  Relation:",
        support.get(
            "relation"
        ),
    )

    print(
        "  Relation supported:",
        support.get(
            "relation_supported"
        ),
    )


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    print(
        "\n"
        + "=" * 72
    )

    print(
        "AI PROJECT - PERFORMANCE PROFILE V1"
    )

    print(
        "=" * 72
    )

    print(
        "\nInitializing pipeline...\n"
    )

    init_start = time.perf_counter()

    pipeline = initialize_pipeline(
        verbose=True,
    )

    initialization_time = (
        time.perf_counter()
        - init_start
    )

    print(
        "\nInitialization time:",
        format_seconds(
            initialization_time
        ),
    )

    print(
        "\nRunning performance profile...\n"
    )

    profile_results = []

    for index, case in enumerate(
        PROFILE_CASES,
        start=1,
    ):
        print(
            "=" * 72
        )

        print(
            f"[{index}/"
            f"{len(PROFILE_CASES)}] "
            f"{case['name']}"
        )

        print(
            "Question:",
            case[
                "question"
            ],
        )

        result = profile_case(
            pipeline,
            case,
            runs=3,
        )

        profile_results.append(
            result
        )

        print(
            "Router:",
            result[
                "router"
            ],
        )

        print(
            "Retriever:",
            result[
                "retriever"
            ],
        )

        print(
            "Answer type:",
            result[
                "answer_type"
            ],
        )

        print(
            "Supported:",
            result[
                "supported"
            ],
        )

        print(
            "Runs:",
            ", ".join(
                format_seconds(
                    value
                )
                for value in result[
                    "timings"
                ]
            ),
        )

        print(
            "Average:",
            format_seconds(
                result[
                    "average"
                ]
            ),
        )

        print(
            "Minimum:",
            format_seconds(
                result[
                    "minimum"
                ]
            ),
        )

        print(
            "Maximum:",
            format_seconds(
                result[
                    "maximum"
                ]
            ),
        )

        if (
            result[
                "retrieval_score"
            ]
            is not None
        ):
            print(
                "Retrieval score:",
                result[
                    "retrieval_score"
                ],
            )

        print_comparison_details(
            result
        )

        print_reasoning_support(
            result
        )

        print()

    # --------------------------------------------------
    # Overall statistics
    # --------------------------------------------------

    print(
        "\n"
        + "=" * 72
    )

    print(
        "OVERALL PERFORMANCE"
    )

    print(
        "=" * 72
    )

    averages = [
        result[
            "average"
        ]
        for result in profile_results
    ]

    if averages:
        overall_average = mean(
            averages
        )

        slowest = max(
            profile_results,
            key=lambda item:
                item[
                    "average"
                ],
        )

        fastest = min(
            profile_results,
            key=lambda item:
                item[
                    "average"
                ],
        )

    else:
        overall_average = 0.0

        slowest = None
        fastest = None

    print(
        "Initialization:",
        format_seconds(
            initialization_time
        ),
    )

    print(
        "Average query time:",
        format_seconds(
            overall_average
        ),
    )

    if fastest:
        print(
            "Fastest:",
            fastest[
                "name"
            ],
            format_seconds(
                fastest[
                    "average"
                ]
            ),
        )

    if slowest:
        print(
            "Slowest:",
            slowest[
                "name"
            ],
            format_seconds(
                slowest[
                    "average"
                ]
            ),
        )

    # --------------------------------------------------
    # Ranking
    # --------------------------------------------------

    print(
        "\n"
        + "-" * 72
    )

    print(
        "LATENCY RANKING"
    )

    print(
        "-" * 72
    )

    ranked = sorted(
        profile_results,
        key=lambda item:
            item[
                "average"
            ],
        reverse=True,
    )

    for index, result in enumerate(
        ranked,
        start=1,
    ):
        print(
            f"{index:>2}. "
            f"{result['name']:<20} "
            f"{format_seconds(result['average'])}"
        )

    print(
        "\n"
        + "=" * 72
    )

    print(
        "PROFILE COMPLETE"
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":
    main()
    