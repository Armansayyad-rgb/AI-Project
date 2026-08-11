import time
from collections import defaultdict

from rag_chat_v2 import (
    initialize_pipeline,
    answer_question,
)


# ==================================================
# Configuration
# ==================================================

UNSUPPORTED_TEXT = (
    "couldn't find enough reliable evidence"
)

MAX_ACCEPTABLE_LATENCY = 5.0


# ==================================================
# Evaluation dataset
# ==================================================

EVALUATION_CASES = [

    # ==================================================
    # CAUSAL REASONING
    # ==================================================

    {
        "id": "causal_001",
        "category": "causal",
        "question": "Why did the Roman Empire decline?",
        "expected_types": ["causal"],
        "expected_supported": True,
        "must_contain_any": [
            "Roman Empire",
            "empire",
        ],
    },
    {
        "id": "causal_002",
        "category": "causal",
        "question": "What caused the Roman Empire to decline?",
        "expected_types": ["causal"],
        "expected_supported": True,
        "must_contain_any": [
            "Roman Empire",
            "empire",
        ],
    },
    {
        "id": "causal_003",
        "category": "causal",
        "question": "What led to the decline of the Roman Empire?",
        "expected_types": ["causal"],
        "expected_supported": True,
        "must_contain_any": [
            "Roman Empire",
            "empire",
        ],
    },

    # ==================================================
    # CHANGE / TEMPORAL REASONING
    # ==================================================

    {
        "id": "change_001",
        "category": "change",
        "question": "How did the Roman Empire change over time?",
        "expected_types": ["change"],
        "expected_supported": True,
        "must_contain_any": [
            "Roman Empire",
            "empire",
        ],
    },
    {
        "id": "change_002",
        "category": "change",
        "question": "How did the Roman Empire evolve?",
        "expected_types": ["change"],
        "expected_supported": True,
        "must_contain_any": [
            "Roman Empire",
            "empire",
        ],
    },

    # ==================================================
    # EFFECT REASONING
    # ==================================================

    {
        "id": "effect_001",
        "category": "effect",
        "question": (
            "What were the effects of the fall "
            "of the Roman Empire?"
        ),
        "expected_types": ["effect"],
        "expected_supported": True,
        "must_contain_any": [
            "Roman Empire",
            "empire",
        ],
    },

    # ==================================================
    # STRUCTURE
    # ==================================================

    {
        "id": "structure_001",
        "category": "structure",
        "question": "How was the Roman army organized?",
        "expected_types": ["structure"],
        "expected_supported": True,
        "must_contain_all": [
            "cohort",
        ],
        "must_contain_any": [
            "century",
            "centuries",
            "legion",
        ],
    },
    {
        "id": "structure_002",
        "category": "structure",
        "question": (
            "Describe how the Roman army "
            "was organized."
        ),
        "expected_types": ["structure"],
        "expected_supported": True,
        "must_contain_any": [
            "cohort",
            "legion",
        ],
    },
    {
        "id": "structure_003",
        "category": "structure",
        "question": "Explain the structure of DNA.",
        "expected_types": ["structure"],
        "expected_supported": True,
        "must_contain_all": [
            "adenine",
            "thymine",
        ],
        "must_contain_any": [
            "double-stranded",
            "double",
        ],
    },

    # ==================================================
    # SUMMARY / EXPLANATION
    # ==================================================

    {
        "id": "summary_001",
        "category": "summary",
        "question": "Explain how photosynthesis works.",
        "expected_types": ["summary"],
        "expected_supported": True,
        "must_contain_all": [
            "sunlight",
            "carbon dioxide",
        ],
        "must_contain_any": [
            "oxygen",
            "sugar",
            "sugars",
        ],
    },
    {
        "id": "summary_002",
        "category": "summary",
        "question": "How does photosynthesis work?",
        "expected_types": ["summary"],
        "expected_supported": True,
        "must_contain_all": [
            "sunlight",
            "carbon dioxide",
        ],
    },
    {
        "id": "summary_003",
        "category": "summary",
        "question": (
            "What is the significance of "
            "the Magna Carta?"
        ),
        "expected_types": ["summary"],
        "expected_supported": True,
        "must_contain_any": [
            "limited royal power",
            "royal power",
        ],
    },
    {
        "id": "summary_004",
        "category": "summary",
        "question": "Why was the Magna Carta important?",
        "expected_types": ["summary"],
        "expected_supported": True,
        "must_contain_any": [
            "royal power",
            "limited",
        ],
    },
    {
        "id": "summary_005",
        "category": "summary",
        "question": "Why is the Magna Carta important?",
        "expected_types": ["summary"],
        "expected_supported": True,
        "must_contain_any": [
            "royal power",
            "limited",
        ],
    },

    # ==================================================
    # ENTITY LIST
    # ==================================================

    {
        "id": "entity_001",
        "category": "entity_list",
        "question": (
            "Who were the main leaders of "
            "the French Revolution?"
        ),
        "expected_types": ["entity_list"],
        "expected_supported": True,
        "must_contain_all": [
            "Robespierre",
            "Danton",
        ],
    },
    {
        "id": "entity_002",
        "category": "entity_list",
        "question": (
            "Who were the key figures of "
            "the French Revolution?"
        ),
        "expected_types": ["entity_list"],
        "expected_supported": True,
        "must_contain_any": [
            "Robespierre",
            "Danton",
        ],
    },

    # ==================================================
    # COMPARISON
    # ==================================================

    {
        "id": "comparison_001",
        "category": "comparison",
        "question": (
            "What are the differences between "
            "mitosis and meiosis?"
        ),
        "expected_types": ["comparison"],
        "expected_supported": True,
        "must_contain_all": [
            "mitosis",
            "meiosis",
        ],
        "must_contain_any": [
            "haploid",
            "diploid",
        ],
    },
    {
        "id": "comparison_002",
        "category": "comparison",
        "question": (
            "How are mitosis and meiosis different?"
        ),
        "expected_types": ["comparison"],
        "expected_supported": True,
        "must_contain_all": [
            "mitosis",
            "meiosis",
        ],
    },
    {
        "id": "comparison_003",
        "category": "comparison",
        "question": (
            "Compare mitosis with meiosis."
        ),
        "expected_types": ["comparison"],
        "expected_supported": True,
        "must_contain_all": [
            "mitosis",
            "meiosis",
        ],
    },

    # ==================================================
    # UNSUPPORTED FACTS
    # ==================================================

    {
        "id": "unsupported_001",
        "category": "unsupported",
        "question": "When was Albert Einstein born?",
        "expected_types": ["system"],
        "expected_supported": False,
        "must_contain_all": [
            UNSUPPORTED_TEXT,
        ],
    },

    # ==================================================
    # FALSE RELATIONS
    # ==================================================

    {
        "id": "false_relation_001",
        "category": "false_relation",
        "question": (
            "How did DNA lead to the Roman Empire?"
        ),
        "expected_types": ["system"],
        "expected_supported": False,
        "must_contain_all": [
            UNSUPPORTED_TEXT,
        ],
    },
    {
        "id": "false_relation_002",
        "category": "false_relation",
        "question": (
            "Why did DNA cause the Roman Empire?"
        ),
        "expected_types": ["system"],
        "expected_supported": False,
        "must_contain_all": [
            UNSUPPORTED_TEXT,
        ],
    },
    {
        "id": "false_relation_003",
        "category": "false_relation",
        "question": (
            "Why did the Magna Carta cause "
            "photosynthesis?"
        ),
        "expected_types": ["system"],
        "expected_supported": False,
        "must_contain_all": [
            UNSUPPORTED_TEXT,
        ],
    },
    {
        "id": "false_relation_004",
        "category": "false_relation",
        "question": (
            "How did the Magna Carta lead "
            "to photosynthesis?"
        ),
        "expected_types": ["system"],
        "expected_supported": False,
        "must_contain_all": [
            UNSUPPORTED_TEXT,
        ],
    },

    # ==================================================
    # FALSE CLAIMS
    # ==================================================

    {
        "id": "false_claim_001",
        "category": "false_claim",
        "question": (
            "Explain why Albert Einstein "
            "invented the telephone."
        ),
        "expected_types": ["system"],
        "expected_supported": False,
        "must_contain_all": [
            UNSUPPORTED_TEXT,
        ],
    },
    {
        "id": "false_claim_002",
        "category": "false_claim",
        "question": (
            "Why did Albert Einstein invent "
            "the telephone?"
        ),
        "expected_types": ["system"],
        "expected_supported": False,
        "must_contain_all": [
            UNSUPPORTED_TEXT,
        ],
    },

    # ==================================================
    # ADVERSARIAL FALSE-PREMISE PHRASING
    # ==================================================

    {
        "id": "adversarial_001",
        "category": "adversarial",
        "question": (
            "Explain the process by which DNA "
            "created the Roman Empire."
        ),
        "expected_types": ["system"],
        "expected_supported": False,
        "must_contain_all": [
            UNSUPPORTED_TEXT,
        ],
    },
    {
        "id": "adversarial_002",
        "category": "adversarial",
        "question": (
            "Describe how the Magna Carta "
            "produced photosynthesis."
        ),
        "expected_types": ["system"],
        "expected_supported": False,
        "must_contain_all": [
            UNSUPPORTED_TEXT,
        ],
    },
    {
        "id": "adversarial_003",
        "category": "adversarial",
        "question": (
            "What role did Albert Einstein play "
            "in inventing the telephone?"
        ),
        "expected_types": ["system"],
        "expected_supported": False,
        "must_contain_all": [
            UNSUPPORTED_TEXT,
        ],
    },
]


# ==================================================
# Text checks
# ==================================================

def contains_text(
    answer,
    expected,
):
    return (
        expected.lower()
        in answer.lower()
    )


def check_required_content(
    answer,
    case,
):
    missing_all = []

    must_contain_all = case.get(
        "must_contain_all",
        [],
    )

    for expected in must_contain_all:
        if not contains_text(
            answer,
            expected,
        ):
            missing_all.append(
                expected
            )

    must_contain_any = case.get(
        "must_contain_any",
        [],
    )

    any_ok = True

    if must_contain_any:
        any_ok = any(
            contains_text(
                answer,
                expected,
            )
            for expected in must_contain_any
        )

    return {
        "all_ok":
            not missing_all,

        "any_ok":
            any_ok,

        "missing_all":
            missing_all,

        "expected_any":
            must_contain_any,
    }


def check_forbidden_content(
    answer,
    case,
):
    found = []

    for forbidden in case.get(
        "must_not_contain",
        [],
    ):
        if contains_text(
            answer,
            forbidden,
        ):
            found.append(
                forbidden
            )

    return found


# ==================================================
# Individual evaluation
# ==================================================

def evaluate_case(
    pipeline,
    case,
):
    start = time.perf_counter()

    result = answer_question(
        pipeline,
        case[
            "question"
        ],
        verbose=False,
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    answer = (
        result.get(
            "answer",
            "",
        )
        or ""
    )

    actual_type = result.get(
        "answer_type"
    )

    actual_supported = result.get(
        "supported"
    )

    expected_types = case.get(
        "expected_types",
        [],
    )

    expected_supported = case.get(
        "expected_supported"
    )

    type_ok = (
        not expected_types
        or actual_type
        in expected_types
    )

    support_ok = (
        expected_supported is None
        or actual_supported
        == expected_supported
    )

    content = check_required_content(
        answer,
        case,
    )

    forbidden = check_forbidden_content(
        answer,
        case,
    )

    latency_ok = (
        elapsed
        <= case.get(
            "max_latency",
            MAX_ACCEPTABLE_LATENCY,
        )
    )

    semantic_ok = (
        type_ok
        and support_ok
        and content[
            "all_ok"
        ]
        and content[
            "any_ok"
        ]
        and not forbidden
    )

    return {
        "id":
            case[
                "id"
            ],

        "category":
            case[
                "category"
            ],

        "question":
            case[
                "question"
            ],

        "answer":
            answer,

        "actual_type":
            actual_type,

        "expected_types":
            expected_types,

        "actual_supported":
            actual_supported,

        "expected_supported":
            expected_supported,

        "router":
            result.get(
                "router"
            ),

        "retriever":
            result.get(
                "retriever"
            ),

        "mode":
            result.get(
                "mode"
            ),

        "type_ok":
            type_ok,

        "support_ok":
            support_ok,

        "content_all_ok":
            content[
                "all_ok"
            ],

        "content_any_ok":
            content[
                "any_ok"
            ],

        "missing_all":
            content[
                "missing_all"
            ],

        "expected_any":
            content[
                "expected_any"
            ],

        "forbidden":
            forbidden,

        "semantic_ok":
            semantic_ok,

        "latency_ok":
            latency_ok,

        "elapsed":
            elapsed,

        "raw_result":
            result,
    }


# ==================================================
# Metric calculation
# ==================================================

def percentage(
    numerator,
    denominator,
):
    if denominator == 0:
        return 0.0

    return (
        numerator
        / denominator
        * 100.0
    )


def calculate_metrics(
    results,
):
    total = len(
        results
    )

    semantic_passes = sum(
        1
        for result in results
        if result[
            "semantic_ok"
        ]
    )

    type_passes = sum(
        1
        for result in results
        if result[
            "type_ok"
        ]
    )

    support_passes = sum(
        1
        for result in results
        if result[
            "support_ok"
        ]
    )

    content_passes = sum(
        1
        for result in results
        if (
            result[
                "content_all_ok"
            ]
            and result[
                "content_any_ok"
            ]
            and not result[
                "forbidden"
            ]
        )
    )

    latency_passes = sum(
        1
        for result in results
        if result[
            "latency_ok"
        ]
    )

    if results:
        average_latency = (
            sum(
                result[
                    "elapsed"
                ]
                for result in results
            )
            / total
        )

        slowest = max(
            results,
            key=lambda result:
                result[
                    "elapsed"
                ],
        )

    else:
        average_latency = 0.0
        slowest = None

    return {
        "total":
            total,

        "semantic_passes":
            semantic_passes,

        "semantic_accuracy":
            percentage(
                semantic_passes,
                total,
            ),

        "type_accuracy":
            percentage(
                type_passes,
                total,
            ),

        "support_accuracy":
            percentage(
                support_passes,
                total,
            ),

        "content_accuracy":
            percentage(
                content_passes,
                total,
            ),

        "latency_pass_rate":
            percentage(
                latency_passes,
                total,
            ),

        "average_latency":
            average_latency,

        "slowest":
            slowest,
    }


# ==================================================
# Category metrics
# ==================================================

def group_by_category(
    results,
):
    grouped = defaultdict(
        list
    )

    for result in results:
        grouped[
            result[
                "category"
            ]
        ].append(
            result
        )

    return grouped


def print_category_metrics(
    results,
):
    grouped = group_by_category(
        results
    )

    print(
        "\n"
        + "=" * 72
    )

    print(
        "CATEGORY RESULTS"
    )

    print(
        "=" * 72
    )

    for category in sorted(
        grouped
    ):
        category_results = (
            grouped[
                category
            ]
        )

        metrics = calculate_metrics(
            category_results
        )

        print(
            f"{category:<20} "
            f"{metrics['semantic_passes']:>3}/"
            f"{metrics['total']:<3} "
            f"{metrics['semantic_accuracy']:>6.1f}% "
            f"avg={metrics['average_latency']:.3f}s"
        )


# ==================================================
# False-premise metric
# ==================================================

def calculate_false_premise_rejection(
    results,
):
    categories = {
        "false_relation",
        "false_claim",
        "adversarial",
    }

    relevant = [
        result
        for result in results
        if result[
            "category"
        ]
        in categories
    ]

    if not relevant:
        return {
            "correct": 0,
            "total": 0,
            "rate": 0.0,
        }

    correct = sum(
        1
        for result in relevant
        if (
            result[
                "actual_type"
            ]
            == "system"
            and result[
                "actual_supported"
            ]
            is False
        )
    )

    return {
        "correct":
            correct,

        "total":
            len(
                relevant
            ),

        "rate":
            percentage(
                correct,
                len(
                    relevant
                ),
            ),
    }


# ==================================================
# Supported-answer metric
# ==================================================

def calculate_supported_acceptance(
    results,
):
    relevant = [
        result
        for result in results
        if result[
            "expected_supported"
        ]
        is True
    ]

    if not relevant:
        return {
            "correct": 0,
            "total": 0,
            "rate": 0.0,
        }

    correct = sum(
        1
        for result in relevant
        if result[
            "actual_supported"
        ]
        is True
    )

    return {
        "correct":
            correct,

        "total":
            len(
                relevant
            ),

        "rate":
            percentage(
                correct,
                len(
                    relevant
                ),
            ),
    }


# ==================================================
# Failure reporting
# ==================================================

def print_failure(
    result,
):
    print(
        "\n"
        + "-" * 72
    )

    print(
        "FAILED:",
        result[
            "id"
        ],
    )

    print(
        "Category:",
        result[
            "category"
        ],
    )

    print(
        "Question:",
        result[
            "question"
        ],
    )

    print(
        "Expected type:",
        result[
            "expected_types"
        ],
    )

    print(
        "Actual type:",
        result[
            "actual_type"
        ],
    )

    print(
        "Expected supported:",
        result[
            "expected_supported"
        ],
    )

    print(
        "Actual supported:",
        result[
            "actual_supported"
        ],
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
        "Mode:",
        result[
            "mode"
        ],
    )

    print(
        "Latency:",
        f"{result['elapsed']:.3f}s",
    )

    if result[
        "missing_all"
    ]:
        print(
            "Missing required:",
            result[
                "missing_all"
            ],
        )

    if (
        result[
            "expected_any"
        ]
        and not result[
            "content_any_ok"
        ]
    ):
        print(
            "Expected at least one:",
            result[
                "expected_any"
            ],
        )

    if result[
        "forbidden"
    ]:
        print(
            "Forbidden content:",
            result[
                "forbidden"
            ],
        )

    print(
        "\nAnswer:"
    )

    print(
        result[
            "answer"
        ]
    )


# ==================================================
# Main evaluation
# ==================================================

def main():
    print(
        "\n"
        + "=" * 72
    )

    print(
        "AI PROJECT - EVALUATION SUITE V1"
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
        "\nRunning",
        len(
            EVALUATION_CASES
        ),
        "evaluation cases...\n",
    )

    results = []

    for index, case in enumerate(
        EVALUATION_CASES,
        start=1,
    ):
        print(
            f"[{index:02d}/"
            f"{len(EVALUATION_CASES):02d}] "
            f"{case['id']:<25}",
            end=" ",
            flush=True,
        )

        result = evaluate_case(
            pipeline,
            case,
        )

        results.append(
            result
        )

        if result[
            "semantic_ok"
        ]:
            status = "PASS"
        else:
            status = "FAIL"

        print(
            f"{status:<4} "
            f"{result['elapsed']:.3f}s "
            f"type={result['actual_type']} "
            f"supported="
            f"{result['actual_supported']}"
        )

    metrics = calculate_metrics(
        results
    )

    false_premise = (
        calculate_false_premise_rejection(
            results
        )
    )

    supported_acceptance = (
        calculate_supported_acceptance(
            results
        )
    )

    print_category_metrics(
        results
    )

    print(
        "\n"
        + "=" * 72
    )

    print(
        "CORE METRICS"
    )

    print(
        "=" * 72
    )

    print(
        f"Semantic accuracy:        "
        f"{metrics['semantic_accuracy']:.1f}% "
        f"({metrics['semantic_passes']}/"
        f"{metrics['total']})"
    )

    print(
        f"Answer-type accuracy:     "
        f"{metrics['type_accuracy']:.1f}%"
    )

    print(
        f"Support-state accuracy:   "
        f"{metrics['support_accuracy']:.1f}%"
    )

    print(
        f"Content accuracy:         "
        f"{metrics['content_accuracy']:.1f}%"
    )

    print(
        f"Latency pass rate:        "
        f"{metrics['latency_pass_rate']:.1f}%"
    )

    print(
        f"Average query latency:    "
        f"{metrics['average_latency']:.3f}s"
    )

    print(
        f"Initialization time:      "
        f"{initialization_time:.3f}s"
    )

    if metrics[
        "slowest"
    ]:
        print(
            f"Slowest query:            "
            f"{metrics['slowest']['id']} "
            f"({metrics['slowest']['elapsed']:.3f}s)"
        )

    print(
        "\nFalse-premise rejection:  "
        f"{false_premise['rate']:.1f}% "
        f"({false_premise['correct']}/"
        f"{false_premise['total']})"
    )

    print(
        "Supported acceptance:     "
        f"{supported_acceptance['rate']:.1f}% "
        f"({supported_acceptance['correct']}/"
        f"{supported_acceptance['total']})"
    )

    failures = [
        result
        for result in results
        if not result[
            "semantic_ok"
        ]
    ]

    if failures:

        print(
            "\n"
            + "=" * 72
        )

        print(
            "FAILURE ANALYSIS"
        )

        print(
            "=" * 72
        )

        for result in failures:
            print_failure(
                result
            )

    print(
        "\n"
        + "=" * 72
    )

    if not failures:
        print(
            "EVALUATION STATUS: PASS"
        )

    else:
        print(
            "EVALUATION STATUS: "
            f"{len(failures)} FAILURE(S)"
        )

    print(
        "=" * 72
    )


if __name__ == "__main__":
    main()