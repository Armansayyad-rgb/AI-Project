import statistics
import time

from rag_chat_v2 import (
    initialize_pipeline,
    answer_question,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

LATENCY_LIMIT_SECONDS = 2.50

TARGET_SEMANTIC_ACCURACY = 0.95
TARGET_TYPE_ACCURACY = 0.95
TARGET_SUPPORT_ACCURACY = 0.95
TARGET_FALSE_PREMISE_REJECTION = 0.95
TARGET_SUPPORTED_ACCEPTANCE = 0.95


# ==========================================================
# TEST CASE HELPERS
# ==========================================================

def case(
    name,
    category,
    question,
    answer_type,
    supported,
    must_contain=None,
    must_not_contain=None,
):
    return {
        "name":
            name,

        "category":
            category,

        "question":
            question,

        "answer_type":
            answer_type,

        "supported":
            supported,

        "must_contain":
            must_contain or [],

        "must_not_contain":
            must_not_contain or [],
    }


# ==========================================================
# EVALUATION CASES
# ==========================================================

TESTS = [

    # ======================================================
    # CAUSAL
    # ======================================================

    case(
        "causal_001",
        "causal",
        "Why did the Roman Empire decline?",
        "causal",
        True,
        [
            "Roman Empire",
            "declin",
        ],
    ),

    case(
        "causal_002",
        "causal",
        "What caused the Roman Empire to decline?",
        "causal",
        True,
        [
            "Roman Empire",
        ],
    ),

    case(
        "causal_003",
        "causal",
        "What led to the decline of the Roman Empire?",
        "causal",
        True,
        [
            "Roman Empire",
        ],
    ),

    case(
        "causal_004",
        "causal",
        "What factors contributed to the decline of the Roman Empire?",
        "causal",
        True,
        [
            "Roman Empire",
        ],
    ),

    case(
        "causal_005",
        "causal",
        "Why did the Roman Empire weaken?",
        "causal",
        True,
        [
            "Roman Empire",
        ],
    ),

    # ======================================================
    # CHANGE
    # ======================================================

    case(
        "change_001",
        "change",
        "How did the Roman Empire change over time?",
        "change",
        True,
        [
            "Roman Empire",
        ],
    ),

    case(
        "change_002",
        "change",
        "How did the Roman Empire evolve?",
        "change",
        True,
        [
            "Roman Empire",
        ],
    ),

    case(
        "change_003",
        "change",
        "How did the Roman Empire develop?",
        "change",
        True,
        [
            "Roman Empire",
        ],
    ),

    case(
        "change_004",
        "change",
        "Describe how the Roman Empire changed.",
        "change",
        True,
        [
            "Roman Empire",
        ],
    ),

    # ======================================================
    # EFFECT
    # ======================================================

    case(
        "effect_001",
        "effect",
        "What were the effects of the fall of the Roman Empire?",
        "effect",
        True,
        [
            "Roman Empire",
        ],
    ),

    case(
        "effect_002",
        "effect",
        "What were the consequences of the fall of the Roman Empire?",
        "effect",
        True,
        [
            "Roman Empire",
        ],
    ),

    case(
        "effect_003",
        "effect",
        "What happened after the fall of the Roman Empire?",
        "effect",
        True,
        [
            "Roman Empire",
        ],
    ),

    case(
        "effect_004",
        "effect",
        "What resulted from the fall of the Roman Empire?",
        "effect",
        True,
        [
            "Roman Empire",
        ],
    ),

    # ======================================================
    # STRUCTURE
    # ======================================================

    case(
        "structure_001",
        "structure",
        "How was the Roman army organized?",
        "structure",
        True,
        [
            "cohort",
            "centur",
        ],
    ),

    case(
        "structure_002",
        "structure",
        "Describe how the Roman army was organized.",
        "structure",
        True,
        [
            "legion",
            "cohort",
        ],
    ),

    case(
        "structure_003",
        "structure",
        "Explain the structure of DNA.",
        "structure",
        True,
        [
            "double",
            "DNA",
        ],
    ),

    case(
        "structure_004",
        "structure",
        "What is the structure of DNA?",
        "structure",
        True,
        [
            "DNA",
        ],
    ),

    case(
        "structure_005",
        "structure",
        "What are the components of DNA?",
        "structure",
        True,
        [
            "DNA",
        ],
    ),

    case(
        "structure_006",
        "structure",
        "What are the parts of the Roman army?",
        "structure",
        True,
        [
            "cohort",
        ],
    ),

    # ======================================================
    # PROCESS / SUMMARY
    # ======================================================

    case(
        "summary_001",
        "summary",
        "Explain how photosynthesis works.",
        "summary",
        True,
        [
            "sunlight",
            "carbon dioxide",
        ],
    ),

    case(
        "summary_002",
        "summary",
        "How does photosynthesis work?",
        "summary",
        True,
        [
            "sunlight",
        ],
    ),

    case(
        "summary_003",
        "summary",
        "Explain the process of photosynthesis.",
        "summary",
        True,
        [
            "photosynthesis",
        ],
    ),

    case(
        "summary_004",
        "summary",
        "Describe photosynthesis.",
        "summary",
        True,
        [
            "photosynthesis",
        ],
    ),

    case(
        "summary_005",
        "summary",
        "What is the significance of the Magna Carta?",
        "summary",
        True,
        [
            "royal power",
        ],
    ),

    case(
        "summary_006",
        "summary",
        "Why was the Magna Carta important?",
        "summary",
        True,
        [
            "royal power",
        ],
    ),

    case(
        "summary_007",
        "summary",
        "Why is the Magna Carta important?",
        "summary",
        True,
        [
            "royal power",
        ],
    ),

    case(
        "summary_008",
        "summary",
        "What was the importance of the Magna Carta?",
        "summary",
        True,
        [
            "Magna Carta",
        ],
    ),

    # ======================================================
    # FEATURES
    # ======================================================

    case(
        "features_001",
        "features",
        "What were the main features of the Roman Republic?",
        "summary",
        True,
        [
            "Senate",
        ],
    ),

    case(
        "features_002",
        "features",
        "What were the features of the Roman Republic?",
        "summary",
        True,
        [
            "Roman",
        ],
    ),

    case(
        "features_003",
        "features",
        "What were the characteristics of the Roman Republic?",
        "summary",
        True,
        [
            "Roman",
        ],
    ),

    # ======================================================
    # ENTITY LIST
    # ======================================================

    case(
        "entity_001",
        "entity_list",
        "Who were the main leaders of the French Revolution?",
        "entity_list",
        True,
        [
            "Robespierre",
            "Danton",
        ],
    ),

    case(
        "entity_002",
        "entity_list",
        "Who were the key figures of the French Revolution?",
        "entity_list",
        True,
        [
            "Robespierre",
            "Danton",
        ],
    ),

    case(
        "entity_003",
        "entity_list",
        "Who were the key leaders of the French Revolution?",
        "entity_list",
        True,
        [
            "Robespierre",
        ],
    ),

    case(
        "entity_004",
        "entity_list",
        "Who were the main figures of the French Revolution?",
        "entity_list",
        True,
        [
            "Danton",
        ],
    ),

    # ======================================================
    # COMPARISON
    # ======================================================

    case(
        "comparison_001",
        "comparison",
        "What are the differences between mitosis and meiosis?",
        "comparison",
        True,
        [
            "mitosis",
            "meiosis",
        ],
    ),

    case(
        "comparison_002",
        "comparison",
        "How are mitosis and meiosis different?",
        "comparison",
        True,
        [
            "mitosis",
            "meiosis",
        ],
    ),

    case(
        "comparison_003",
        "comparison",
        "Compare mitosis and meiosis.",
        "comparison",
        True,
        [
            "mitosis",
            "meiosis",
        ],
    ),

    case(
        "comparison_004",
        "comparison",
        "Compare mitosis with meiosis.",
        "comparison",
        True,
        [
            "mitosis",
            "meiosis",
        ],
    ),

    case(
        "comparison_005",
        "comparison",
        "Mitosis versus meiosis.",
        "comparison",
        True,
        [
            "mitosis",
            "meiosis",
        ],
    ),

    # ======================================================
    # EXTRACTOR / UNSUPPORTED
    # ======================================================

    case(
        "unsupported_001",
        "unsupported",
        "When was Albert Einstein born?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "unsupported_002",
        "unsupported",
        "When was Albert Einstein founded?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "unsupported_003",
        "unsupported",
        "When was the Magna Carta released?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    # ======================================================
    # FALSE RELATION
    # ======================================================

    case(
        "false_relation_001",
        "false_relation",
        "How did DNA lead to the Roman Empire?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_relation_002",
        "false_relation",
        "Why did the Magna Carta cause photosynthesis?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_relation_003",
        "false_relation",
        "How did photosynthesis create the Roman army?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_relation_004",
        "false_relation",
        "Why did meiosis cause the fall of the Roman Empire?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_relation_005",
        "false_relation",
        "How did the French Revolution create DNA?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_relation_006",
        "false_relation",
        "What effect did DNA have on the Magna Carta?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_relation_007",
        "false_relation",
        "How did photosynthesis lead to the French Revolution?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_relation_008",
        "false_relation",
        "Why did mitosis cause the Roman Republic?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    # ======================================================
    # FALSE CLAIM
    # ======================================================

    case(
        "false_claim_001",
        "false_claim",
        "Explain why Albert Einstein invented the telephone.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_claim_002",
        "false_claim",
        "Describe how Albert Einstein invented the telephone.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_claim_003",
        "false_claim",
        "Explain why the Magna Carta invented democracy.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_claim_004",
        "false_claim",
        "Explain why DNA invented photosynthesis.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_claim_005",
        "false_claim",
        "Describe how mitosis invented meiosis.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "false_claim_006",
        "false_claim",
        "Explain why the Roman Empire invented DNA.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    # ======================================================
    # ADVERSARIAL
    # ======================================================

    case(
        "adversarial_001",
        "adversarial",
        "Explain the process by which DNA created the Roman Empire.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "adversarial_002",
        "adversarial",
        "Describe how the Magna Carta produced photosynthesis.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "adversarial_003",
        "adversarial",
        "Explain how the Roman Empire functioned as a DNA molecule.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "adversarial_004",
        "adversarial",
        "Describe the structure of photosynthesis as a Roman legion.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "adversarial_005",
        "adversarial",
        "Explain how meiosis caused medieval English law.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "adversarial_006",
        "adversarial",
        "Explain why Roman military cohorts perform photosynthesis.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "adversarial_007",
        "adversarial",
        "Describe how DNA limited royal power in England.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "adversarial_008",
        "adversarial",
        "Explain how the Magna Carta produces haploid cells.",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    # ======================================================
    # NOISY / PARAPHRASE
    # ======================================================

    case(
        "paraphrase_001",
        "paraphrase",
        "What made the Roman Empire eventually decline?",
        "causal",
        True,
        [
            "Roman Empire",
        ],
    ),

    case(
        "paraphrase_002",
        "paraphrase",
        "In what way was the Roman army structured?",
        "structure",
        True,
        [
            "Roman",
        ],
    ),

    case(
        "paraphrase_003",
        "paraphrase",
        "How exactly does photosynthesis operate?",
        "summary",
        True,
        [
            "photosynthesis",
        ],
    ),

    case(
        "paraphrase_004",
        "paraphrase",
        "Why does the Magna Carta matter historically?",
        "summary",
        True,
        [
            "Magna Carta",
        ],
    ),

    case(
        "paraphrase_005",
        "paraphrase",
        "Name the important figures in the French Revolution.",
        "entity_list",
        True,
        [
            "Robespierre",
        ],
    ),

    case(
        "paraphrase_006",
        "paraphrase",
        "What separates mitosis from meiosis?",
        "comparison",
        True,
        [
            "mitosis",
            "meiosis",
        ],
    ),

    # ======================================================
    # ROUTING STRESS
    # ======================================================

    case(
        "routing_001",
        "routing",
        "Why was the Magna Carta important?",
        "summary",
        True,
        [
            "royal power",
        ],
    ),

    case(
        "routing_002",
        "routing",
        "Why did the Roman Empire decline?",
        "causal",
        True,
        [
            "Roman Empire",
        ],
    ),

    case(
        "routing_003",
        "routing",
        "Explain how photosynthesis works.",
        "summary",
        True,
        [
            "photosynthesis",
        ],
    ),

    case(
        "routing_004",
        "routing",
        "Explain the structure of DNA.",
        "structure",
        True,
        [
            "DNA",
        ],
    ),

    case(
        "routing_005",
        "routing",
        "Who were the key figures of the French Revolution?",
        "entity_list",
        True,
        [
            "Robespierre",
        ],
    ),

    # ======================================================
    # MIXED NEGATIVE
    # ======================================================

    case(
        "negative_001",
        "negative",
        "What caused photosynthesis to overthrow the Roman Empire?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "negative_002",
        "negative",
        "Why did DNA sign the Magna Carta?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "negative_003",
        "negative",
        "How did the Roman army split water into oxygen?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "negative_004",
        "negative",
        "How did Robespierre create meiosis?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),

    case(
        "negative_005",
        "negative",
        "Why did chromosomes limit royal power?",
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    ),
]


# ==========================================================
# RESULT CHECKING
# ==========================================================

def text_contains(
    text,
    fragment,
):
    return (
        fragment.lower()
        in text.lower()
    )


def evaluate_case(
    pipeline,
    test,
):
    start = time.perf_counter()

    result = answer_question(
        pipeline,
        test[
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

    answer_type = result.get(
        "answer_type"
    )

    supported = bool(
        result.get(
            "supported",
            False,
        )
    )

    missing_required = []

    for fragment in test[
        "must_contain"
    ]:
        if not text_contains(
            answer,
            fragment,
        ):
            missing_required.append(
                fragment
            )

    forbidden_found = []

    for fragment in test[
        "must_not_contain"
    ]:
        if text_contains(
            answer,
            fragment,
        ):
            forbidden_found.append(
                fragment
            )

    type_ok = (
        answer_type
        == test[
            "answer_type"
        ]
    )

    support_ok = (
        supported
        == test[
            "supported"
        ]
    )

    content_ok = (
        not missing_required
        and not forbidden_found
    )

    latency_ok = (
        elapsed
        <= LATENCY_LIMIT_SECONDS
    )

    semantic_ok = (
        type_ok
        and support_ok
        and content_ok
    )

    return {
        "passed":
            semantic_ok,

        "semantic_ok":
            semantic_ok,

        "type_ok":
            type_ok,

        "support_ok":
            support_ok,

        "content_ok":
            content_ok,

        "latency_ok":
            latency_ok,

        "elapsed":
            elapsed,

        "answer":
            answer,

        "actual_type":
            answer_type,

        "expected_type":
            test[
                "answer_type"
            ],

        "actual_supported":
            supported,

        "expected_supported":
            test[
                "supported"
            ],

        "missing_required":
            missing_required,

        "forbidden_found":
            forbidden_found,

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

        "raw_result":
            result,
    }


# ==========================================================
# PERCENTILE
# ==========================================================

def percentile(
    values,
    percent,
):
    if not values:
        return 0.0

    ordered = sorted(
        values
    )

    if len(
        ordered
    ) == 1:
        return ordered[
            0
        ]

    position = (
        len(
            ordered
        )
        - 1
    ) * percent

    lower = int(
        position
    )

    upper = min(
        lower + 1,
        len(
            ordered
        )
        - 1,
    )

    fraction = (
        position
        - lower
    )

    return (
        ordered[
            lower
        ]
        * (
            1.0
            - fraction
        )
        + ordered[
            upper
        ]
        * fraction
    )


# ==========================================================
# PROGRESS
# ==========================================================

def progress_bucket(
    completed,
    total,
):
    if total <= 0:
        return 100

    percentage = int(
        (
            completed
            / total
        )
        * 100
    )

    return (
        percentage
        // 10
    ) * 10


# ==========================================================
# MAIN EVALUATION
# ==========================================================

def main():
    print(
        "\n"
        + "=" * 76
    )

    print(
        "AI PROJECT - EVALUATION SUITE V2"
    )

    print(
        "=" * 76
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
        f"\nRunning {len(TESTS)} "
        "evaluation cases...\n"
    )

    results = []

    category_stats = {}

    last_progress = 0

    # ------------------------------------------------------
    # Execute tests
    # ------------------------------------------------------

    for index, test in enumerate(
        TESTS,
        start=1,
    ):
        evaluation = evaluate_case(
            pipeline,
            test,
        )

        results.append(
            (
                test,
                evaluation,
            )
        )

        category = test[
            "category"
        ]

        if category not in category_stats:
            category_stats[
                category
            ] = {
                "passed":
                    0,

                "total":
                    0,

                "latencies":
                    [],
            }

        category_stats[
            category
        ][
            "total"
        ] += 1

        category_stats[
            category
        ][
            "latencies"
        ].append(
            evaluation[
                "elapsed"
            ]
        )

        if evaluation[
            "passed"
        ]:
            category_stats[
                category
            ][
                "passed"
            ] += 1

        status = (
            "PASS"
            if evaluation[
                "passed"
            ]
            else "FAIL"
        )

        print(
            f"[{index:03d}/{len(TESTS):03d}] "
            f"{test['name']:<28} "
            f"{status:<4} "
            f"{evaluation['elapsed']:.3f}s "
            f"type="
            f"{evaluation['actual_type']} "
            f"supported="
            f"{evaluation['actual_supported']}"
        )

        # ----------------------------------------------
        # 10% progress reporting
        # ----------------------------------------------

        current_progress = (
            progress_bucket(
                index,
                len(
                    TESTS
                ),
            )
        )

        if (
            current_progress
            >= last_progress + 10
        ):
            last_progress = (
                current_progress
            )

            print(
                f"\n>>> "
                f"{current_progress}% complete"
                f"\n"
            )

    # ==================================================
    # CORE COUNTS
    # ==================================================

    total = len(
        results
    )

    semantic_passes = sum(
        1
        for _, result in results
        if result[
            "semantic_ok"
        ]
    )

    type_passes = sum(
        1
        for _, result in results
        if result[
            "type_ok"
        ]
    )

    support_passes = sum(
        1
        for _, result in results
        if result[
            "support_ok"
        ]
    )

    content_passes = sum(
        1
        for _, result in results
        if result[
            "content_ok"
        ]
    )

    latency_passes = sum(
        1
        for _, result in results
        if result[
            "latency_ok"
        ]
    )

    latencies = [
        result[
            "elapsed"
        ]
        for _, result in results
    ]

    semantic_accuracy = (
        semantic_passes
        / total
        if total
        else 0.0
    )

    type_accuracy = (
        type_passes
        / total
        if total
        else 0.0
    )

    support_accuracy = (
        support_passes
        / total
        if total
        else 0.0
    )

    content_accuracy = (
        content_passes
        / total
        if total
        else 0.0
    )

    latency_pass_rate = (
        latency_passes
        / total
        if total
        else 0.0
    )

    average_latency = (
        statistics.mean(
            latencies
        )
        if latencies
        else 0.0
    )

    median_latency = (
        statistics.median(
            latencies
        )
        if latencies
        else 0.0
    )

    p90_latency = percentile(
        latencies,
        0.90,
    )

    p95_latency = percentile(
        latencies,
        0.95,
    )

    p99_latency = percentile(
        latencies,
        0.99,
    )

    slowest = max(
        results,
        key=lambda pair: (
            pair[
                1
            ][
                "elapsed"
            ]
        ),
    )

    fastest = min(
        results,
        key=lambda pair: (
            pair[
                1
            ][
                "elapsed"
            ]
        ),
    )

    # ==================================================
    # SUPPORT / REJECTION METRICS
    # ==================================================

    negative_cases = [
        (
            test,
            result,
        )
        for test, result in results
        if not test[
            "supported"
        ]
    ]

    supported_cases = [
        (
            test,
            result,
        )
        for test, result in results
        if test[
            "supported"
        ]
    ]

    rejected_negative = sum(
        1
        for _, result in negative_cases
        if (
            result[
                "actual_supported"
            ]
            is False
        )
    )

    accepted_supported = sum(
        1
        for _, result in supported_cases
        if (
            result[
                "actual_supported"
            ]
            is True
        )
    )

    false_premise_rejection = (
        rejected_negative
        / len(
            negative_cases
        )
        if negative_cases
        else 0.0
    )

    supported_acceptance = (
        accepted_supported
        / len(
            supported_cases
        )
        if supported_cases
        else 0.0
    )

    # ==================================================
    # CATEGORY RESULTS
    # ==================================================

    print(
        "\n"
        + "=" * 76
    )

    print(
        "CATEGORY RESULTS"
    )

    print(
        "=" * 76
    )

    for category in sorted(
        category_stats
    ):
        stats = category_stats[
            category
        ]

        average = (
            statistics.mean(
                stats[
                    "latencies"
                ]
            )
            if stats[
                "latencies"
            ]
            else 0.0
        )

        rate = (
            stats[
                "passed"
            ]
            / stats[
                "total"
            ]
        )

        print(
            f"{category:<22} "
            f"{stats['passed']:>3}/"
            f"{stats['total']:<3} "
            f"{rate * 100:>6.1f}% "
            f"avg={average:.3f}s"
        )

    # ==================================================
    # CORE METRICS
    # ==================================================

    print(
        "\n"
        + "=" * 76
    )

    print(
        "CORE METRICS"
    )

    print(
        "=" * 76
    )

    print(
        f"Semantic accuracy:        "
        f"{semantic_accuracy * 100:.1f}% "
        f"({semantic_passes}/{total})"
    )

    print(
        f"Answer-type accuracy:     "
        f"{type_accuracy * 100:.1f}%"
    )

    print(
        f"Support-state accuracy:   "
        f"{support_accuracy * 100:.1f}%"
    )

    print(
        f"Content accuracy:         "
        f"{content_accuracy * 100:.1f}%"
    )

    print(
        f"Latency pass rate:        "
        f"{latency_pass_rate * 100:.1f}%"
    )

    print(
        f"Average query latency:    "
        f"{average_latency:.3f}s"
    )

    print(
        f"Median latency (P50):     "
        f"{median_latency:.3f}s"
    )

    print(
        f"P90 latency:              "
        f"{p90_latency:.3f}s"
    )

    print(
        f"P95 latency:              "
        f"{p95_latency:.3f}s"
    )

    print(
        f"P99 latency:              "
        f"{p99_latency:.3f}s"
    )

    print(
        f"Initialization time:      "
        f"{initialization_time:.3f}s"
    )

    print(
        f"Fastest query:            "
        f"{fastest[0]['name']} "
        f"({fastest[1]['elapsed']:.3f}s)"
    )

    print(
        f"Slowest query:            "
        f"{slowest[0]['name']} "
        f"({slowest[1]['elapsed']:.3f}s)"
    )

    print()

    print(
        f"False-premise rejection:  "
        f"{false_premise_rejection * 100:.1f}% "
        f"({rejected_negative}/"
        f"{len(negative_cases)})"
    )

    print(
        f"Supported acceptance:     "
        f"{supported_acceptance * 100:.1f}% "
        f"({accepted_supported}/"
        f"{len(supported_cases)})"
    )

    # ==================================================
    # TARGET CHECKS
    # ==================================================

    target_checks = {
        "semantic_accuracy":
            semantic_accuracy
            >= TARGET_SEMANTIC_ACCURACY,

        "type_accuracy":
            type_accuracy
            >= TARGET_TYPE_ACCURACY,

        "support_accuracy":
            support_accuracy
            >= TARGET_SUPPORT_ACCURACY,

        "false_premise_rejection":
            false_premise_rejection
            >= TARGET_FALSE_PREMISE_REJECTION,

        "supported_acceptance":
            supported_acceptance
            >= TARGET_SUPPORTED_ACCEPTANCE,
    }

    print(
        "\n"
        + "=" * 76
    )

    print(
        "TARGET STATUS"
    )

    print(
        "=" * 76
    )

    print(
        "Semantic >= 95%:           ",
        (
            "PASS"
            if target_checks[
                "semantic_accuracy"
            ]
            else "FAIL"
        ),
    )

    print(
        "Answer type >= 95%:        ",
        (
            "PASS"
            if target_checks[
                "type_accuracy"
            ]
            else "FAIL"
        ),
    )

    print(
        "Support state >= 95%:      ",
        (
            "PASS"
            if target_checks[
                "support_accuracy"
            ]
            else "FAIL"
        ),
    )

    print(
        "False-premise >= 95%:      ",
        (
            "PASS"
            if target_checks[
                "false_premise_rejection"
            ]
            else "FAIL"
        ),
    )

    print(
        "Supported acceptance >=95%:",
        (
            "PASS"
            if target_checks[
                "supported_acceptance"
            ]
            else "FAIL"
        ),
    )

    # ==================================================
    # FAILURES
    # ==================================================

    failures = [
        (
            test,
            result,
        )
        for test, result in results
        if not result[
            "semantic_ok"
        ]
    ]

    if failures:
        print(
            "\n"
            + "=" * 76
        )

        print(
            "FAILURE ANALYSIS"
        )

        print(
            "=" * 76
        )

        for test, result in failures:

            print(
                "\n"
                + "-" * 76
            )

            print(
                "FAILED:",
                test[
                    "name"
                ],
            )

            print(
                "Category:",
                test[
                    "category"
                ],
            )

            print(
                "Question:",
                test[
                    "question"
                ],
            )

            print(
                "Expected type:",
                test[
                    "answer_type"
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
                test[
                    "supported"
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
                "missing_required"
            ]:
                print(
                    "Missing required:",
                    result[
                        "missing_required"
                    ],
                )

            if result[
                "forbidden_found"
            ]:
                print(
                    "Forbidden content:",
                    result[
                        "forbidden_found"
                    ],
                )

            print(
                "\nAnswer:\n"
            )

            print(
                result[
                    "answer"
                ]
            )

    # ==================================================
    # FINAL STATUS
    # ==================================================

    all_targets_pass = all(
        target_checks.values()
    )

    print(
        "\n"
        + "=" * 76
    )

    if (
        not failures
        and all_targets_pass
    ):
        print(
            "EVALUATION V2 STATUS: PASS"
        )

    elif all_targets_pass:
        print(
            "EVALUATION V2 STATUS: "
            "TARGETS PASS, "
            "BUT CASE FAILURES EXIST"
        )

    else:
        print(
            "EVALUATION V2 STATUS: FAIL"
        )

    print(
        "=" * 76
    )


if __name__ == "__main__":
    main()