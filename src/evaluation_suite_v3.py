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

EXPECTED_TEST_COUNT = 245


# ==========================================================
# TEST CASE HELPER
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
# TEST COLLECTION
# ==========================================================

TESTS = []


def add_case(
    category,
    question,
    answer_type,
    supported,
    must_contain=None,
    must_not_contain=None,
):
    count = sum(
        1
        for item in TESTS
        if item[
            "category"
        ] == category
    ) + 1

    TESTS.append(
        case(
            f"{category}_{count:03d}",
            category,
            question,
            answer_type,
            supported,
            must_contain,
            must_not_contain,
        )
    )


# ==========================================================
# 1. CAUSAL GENERALIZATION
# 20 cases
# ==========================================================

CAUSAL_QUESTIONS = [
    "Why did the Roman Empire decline?",
    "What caused the Roman Empire to decline?",
    "What led to the decline of the Roman Empire?",
    "What made the Roman Empire decline?",
    "What made the Roman Empire eventually decline?",
    "Why did the Roman Empire weaken?",
    "What factors caused the Roman Empire to weaken?",
    "What factors contributed to the Roman Empire's decline?",
    "For what reasons did the Roman Empire decline?",
    "What were the reasons for the Roman Empire's decline?",
    "Why was the Roman Empire declining?",
    "How did the Roman Empire come to decline?",
    "What drove the Roman Empire into decline?",
    "What contributed to the weakening of the Roman Empire?",
    "Why did the Roman Empire eventually weaken?",
    "What brought about the decline of the Roman Empire?",
    "What was behind the decline of the Roman Empire?",
    "Which factors led to the Roman Empire's decline?",
    "Why did the Roman Empire lose strength?",
    "Explain why the Roman Empire declined.",
]

for question in CAUSAL_QUESTIONS:
    add_case(
        "causal",
        question,
        "causal",
        True,
        [
            "Roman Empire",
        ],
    )


# ==========================================================
# 2. CHANGE GENERALIZATION
# 15 cases
# ==========================================================

CHANGE_QUESTIONS = [
    "How did the Roman Empire change over time?",
    "How did the Roman Empire evolve?",
    "How did the Roman Empire develop?",
    "Describe how the Roman Empire changed.",
    "Describe the changes in the Roman Empire over time.",
    "In what ways did the Roman Empire change?",
    "How did the Roman Empire transform over time?",
    "How did the Roman Empire develop over the centuries?",
    "What changes occurred in the Roman Empire over time?",
    "How was the Roman Empire different later in its history?",
    "How did the Roman Empire evolve through history?",
    "Explain how the Roman Empire changed over time.",
    "What developments changed the Roman Empire?",
    "How did the Roman Empire transition over time?",
    "Describe the historical development of the Roman Empire.",
]

for question in CHANGE_QUESTIONS:
    add_case(
        "change",
        question,
        "change",
        True,
        [
            "Roman Empire",
        ],
    )


# ==========================================================
# 3. EFFECT / CONSEQUENCE GENERALIZATION
# 15 cases
# ==========================================================

EFFECT_QUESTIONS = [
    "What were the effects of the fall of the Roman Empire?",
    "What were the consequences of the fall of the Roman Empire?",
    "What happened after the fall of the Roman Empire?",
    "What resulted from the fall of the Roman Empire?",
    "What followed the fall of the Roman Empire?",
    "What was the impact of the fall of the Roman Empire?",
    "What changes followed the fall of the Roman Empire?",
    "What happened as a result of the fall of the Roman Empire?",
    "Describe the consequences of the fall of the Roman Empire.",
    "Explain the effects of the fall of the Roman Empire.",
    "How did conditions change after the Roman Empire fell?",
    "What developments followed the Roman Empire's fall?",
    "What came after the Roman Empire fell?",
    "What consequences followed the collapse of the Roman Empire?",
    "What was one result of the fall of the Roman Empire?",
]

for question in EFFECT_QUESTIONS:
    add_case(
        "effect",
        question,
        "effect",
        True,
        [
            "Roman Empire",
        ],
    )


# ==========================================================
# 4. STRUCTURE - ROMAN ARMY
# 15 cases
# ==========================================================

ROMAN_STRUCTURE_QUESTIONS = [
    "How was the Roman army organized?",
    "Describe how the Roman army was organized.",
    "What was the structure of the Roman army?",
    "What were the parts of the Roman army?",
    "In what way was the Roman army structured?",
    "How was the Roman military organized?",
    "Describe the organization of the Roman army.",
    "How were Roman legions organized?",
    "What units made up the Roman army?",
    "Explain the structure of the Roman army.",
    "How was a Roman legion divided?",
    "What was the hierarchy of the Roman army?",
    "What units formed a Roman legion?",
    "Describe the internal structure of a Roman legion.",
    "How were Roman soldiers organized into units?",
]

for question in ROMAN_STRUCTURE_QUESTIONS:
    add_case(
        "structure",
        question,
        "structure",
        True,
        [
            "cohort",
        ],
    )


# ==========================================================
# 5. STRUCTURE - DNA
# 15 cases
# ==========================================================

DNA_STRUCTURE_QUESTIONS = [
    "Explain the structure of DNA.",
    "What is the structure of DNA?",
    "Describe the structure of DNA.",
    "What are the components of DNA?",
    "What are the parts of DNA?",
    "How is DNA structured?",
    "How is a DNA molecule organized?",
    "Describe how DNA is organized.",
    "What makes up a DNA molecule?",
    "What is DNA made of?",
    "Explain how DNA is structured.",
    "Describe the molecular structure of DNA.",
    "What components form DNA?",
    "How are the parts of DNA arranged?",
    "What does the structure of DNA consist of?",
]

for question in DNA_STRUCTURE_QUESTIONS:
    add_case(
        "structure",
        question,
        "structure",
        True,
        [
            "DNA",
        ],
    )


# ==========================================================
# 6. PROCESS / PHOTOSYNTHESIS
# 20 cases
# ==========================================================

PHOTOSYNTHESIS_QUESTIONS = [
    "Explain how photosynthesis works.",
    "How does photosynthesis work?",
    "Explain the process of photosynthesis.",
    "Describe photosynthesis.",
    "How exactly does photosynthesis operate?",
    "What happens during photosynthesis?",
    "How does the process of photosynthesis operate?",
    "Describe how photosynthesis works.",
    "What is the process of photosynthesis?",
    "Explain what occurs in photosynthesis.",
    "How do plants perform photosynthesis?",
    "What happens when photosynthesis takes place?",
    "Describe the mechanism of photosynthesis.",
    "How does photosynthesis convert energy?",
    "Explain the main process involved in photosynthesis.",
    "What does photosynthesis do?",
    "Explain how sunlight is used in photosynthesis.",
    "How is energy converted during photosynthesis?",
    "Describe the basic operation of photosynthesis.",
    "What are the main steps involved in photosynthesis?",
]

for question in PHOTOSYNTHESIS_QUESTIONS:
    add_case(
        "summary",
        question,
        "summary",
        True,
        [
            "photosynthesis",
        ],
    )


# ==========================================================
# 7. SIGNIFICANCE / MAGNA CARTA
# 15 cases
# ==========================================================

MAGNA_QUESTIONS = [
    "What is the significance of the Magna Carta?",
    "Why was the Magna Carta important?",
    "Why is the Magna Carta important?",
    "What was the importance of the Magna Carta?",
    "Why does the Magna Carta matter historically?",
    "What made the Magna Carta significant?",
    "What was historically important about the Magna Carta?",
    "Explain the significance of the Magna Carta.",
    "Describe the historical importance of the Magna Carta.",
    "Why does the Magna Carta matter?",
    "What impact made the Magna Carta significant?",
    "What was important about the Magna Carta?",
    "How was the Magna Carta historically significant?",
    "Why has the Magna Carta been considered important?",
    "What is historically significant about the Magna Carta?",
]

for question in MAGNA_QUESTIONS:
    add_case(
        "significance",
        question,
        "summary",
        True,
        [
            "royal power",
        ],
    )


# ==========================================================
# 8. FEATURES / ROMAN REPUBLIC
# 15 cases
# ==========================================================

FEATURE_QUESTIONS = [
    "What were the main features of the Roman Republic?",
    "What were the features of the Roman Republic?",
    "What were the characteristics of the Roman Republic?",
    "Describe the main features of the Roman Republic.",
    "What characterized the Roman Republic?",
    "What were important features of the Roman Republic?",
    "Describe the characteristics of the Roman Republic.",
    "What defined the Roman Republic?",
    "What features characterized the Roman Republic?",
    "Explain the main characteristics of the Roman Republic.",
    "What political features did the Roman Republic have?",
    "What institutions characterized the Roman Republic?",
    "What were key characteristics of the Roman Republic?",
    "Describe important institutions of the Roman Republic.",
    "What were the defining features of the Roman Republic?",
]

for question in FEATURE_QUESTIONS:
    add_case(
        "features",
        question,
        "summary",
        True,
        [
            "Roman",
        ],
    )


# ==========================================================
# 9. ENTITY LIST / FRENCH REVOLUTION
# 15 cases
# ==========================================================

ENTITY_QUESTIONS = [
    "Who were the main leaders of the French Revolution?",
    "Who were the key figures of the French Revolution?",
    "Who were the key leaders of the French Revolution?",
    "Who were the main figures of the French Revolution?",
    "Name the important figures in the French Revolution.",
    "Name key figures from the French Revolution.",
    "Who were important people in the French Revolution?",
    "Who were the major leaders of the French Revolution?",
    "Which people were important in the French Revolution?",
    "Who were notable figures in the French Revolution?",
    "List important leaders of the French Revolution.",
    "Which leaders were prominent in the French Revolution?",
    "Who played major roles in the French Revolution?",
    "Who were major political figures in the French Revolution?",
    "Identify key people from the French Revolution.",
]

for question in ENTITY_QUESTIONS:
    add_case(
        "entity_list",
        question,
        "entity_list",
        True,
        [
            "Robespierre",
        ],
    )


# ==========================================================
# 10. COMPARISON
# 20 cases
# ==========================================================

COMPARISON_QUESTIONS = [
    "What are the differences between mitosis and meiosis?",
    "How are mitosis and meiosis different?",
    "Compare mitosis and meiosis.",
    "Compare mitosis with meiosis.",
    "Compare mitosis to meiosis.",
    "Mitosis versus meiosis.",
    "Mitosis vs meiosis.",
    "What separates mitosis from meiosis?",
    "How does mitosis differ from meiosis?",
    "How is mitosis different from meiosis?",
    "What is the difference between mitosis and meiosis?",
    "Differences between mitosis and meiosis.",
    "What differs between mitosis and meiosis?",
    "How does mitosis compare with meiosis?",
    "How does mitosis compare to meiosis?",
    "Explain the differences between mitosis and meiosis.",
    "Describe how mitosis differs from meiosis.",
    "In what ways are mitosis and meiosis different?",
    "What distinguishes mitosis from meiosis?",
    "What are the main differences between mitosis and meiosis?",
]

for question in COMPARISON_QUESTIONS:
    add_case(
        "comparison",
        question,
        "comparison",
        True,
        [
            "mitosis",
            "meiosis",
        ],
    )


# ==========================================================
# 11. UNSUPPORTED FACTS
# 10 cases
# ==========================================================

UNSUPPORTED_QUESTIONS = [
    "When was Albert Einstein born?",
    "When was Albert Einstein founded?",
    "When was Albert Einstein released?",
    "When was Albert Einstein established?",
    "When was the Magna Carta released?",
    "When was DNA founded?",
    "When was photosynthesis founded?",
    "When was mitosis released?",
    "When was meiosis established?",
    "When was the Roman army published?",
]

for question in UNSUPPORTED_QUESTIONS:
    add_case(
        "unsupported",
        question,
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    )


# ==========================================================
# 12. FALSE RELATIONS
# 20 cases
# ==========================================================

FALSE_RELATIONS = [
    "How did DNA lead to the Roman Empire?",
    "Why did the Magna Carta cause photosynthesis?",
    "How did photosynthesis create the Roman army?",
    "Why did meiosis cause the fall of the Roman Empire?",
    "How did the French Revolution create DNA?",
    "What effect did DNA have on the Magna Carta?",
    "How did photosynthesis lead to the French Revolution?",
    "Why did mitosis cause the Roman Republic?",
    "How did DNA produce the Magna Carta?",
    "Why did the Roman army cause meiosis?",
    "How did the Magna Carta create DNA?",
    "Why did photosynthesis cause the French Revolution?",
    "How did mitosis produce the Roman Empire?",
    "Why did DNA cause the Roman army?",
    "How did meiosis create the Magna Carta?",
    "Why did the French Revolution cause photosynthesis?",
    "How did the Roman Empire generate DNA?",
    "Why did chromosomes cause the Magna Carta?",
    "How did the Roman Republic produce meiosis?",
    "Why did photosynthesis create Roman law?",
]

for question in FALSE_RELATIONS:
    add_case(
        "false_relation",
        question,
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    )


# ==========================================================
# 13. FALSE CLAIMS
# 15 cases
# ==========================================================

FALSE_CLAIMS = [
    "Explain why Albert Einstein invented the telephone.",
    "Describe how Albert Einstein invented the telephone.",
    "Explain why the Magna Carta invented democracy.",
    "Explain why DNA invented photosynthesis.",
    "Describe how mitosis invented meiosis.",
    "Explain why the Roman Empire invented DNA.",
    "Explain why Robespierre invented photosynthesis.",
    "Describe how the Roman army invented chromosomes.",
    "Explain why meiosis invented the Magna Carta.",
    "Explain why photosynthesis invented the Roman Republic.",
    "Describe how DNA invented the French Revolution.",
    "Explain why the Roman Senate invented mitosis.",
    "Explain why the Magna Carta invented DNA replication.",
    "Describe how chromosomes invented Roman law.",
    "Explain why the French Revolution invented meiosis.",
]

for question in FALSE_CLAIMS:
    add_case(
        "false_claim",
        question,
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    )


# ==========================================================
# 14. ADVERSARIAL CROSS-DOMAIN
# 20 cases
# ==========================================================

ADVERSARIAL_QUESTIONS = [
    "Explain the process by which DNA created the Roman Empire.",
    "Describe how the Magna Carta produced photosynthesis.",
    "Explain how the Roman Empire functioned as a DNA molecule.",
    "Describe the structure of photosynthesis as a Roman legion.",
    "Explain how meiosis caused medieval English law.",
    "Explain why Roman military cohorts perform photosynthesis.",
    "Describe how DNA limited royal power in England.",
    "Explain how the Magna Carta produces haploid cells.",
    "Describe how chromosomes governed the Roman Republic.",
    "Explain how photosynthesis organized the Roman army.",
    "Describe how meiosis operated as the Roman Senate.",
    "Explain how the French Revolution replicated DNA.",
    "Describe the Roman Empire as a stage of mitosis.",
    "Explain how DNA formed medieval English government.",
    "Describe how the Magna Carta separated chromosomes.",
    "Explain how Roman legions produce oxygen.",
    "Describe how photosynthesis created Robespierre.",
    "Explain how mitosis limited royal authority.",
    "Describe DNA as a political institution of the Roman Republic.",
    "Explain how meiosis caused the Magna Carta to be signed.",
]

for question in ADVERSARIAL_QUESTIONS:
    add_case(
        "adversarial",
        question,
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    )


# ==========================================================
# 15. NEGATIVE LANGUAGE VARIANTS
# 15 cases
# ==========================================================

NEGATIVE_QUESTIONS = [
    "What caused photosynthesis to overthrow the Roman Empire?",
    "Why did DNA sign the Magna Carta?",
    "How did the Roman army split water into oxygen?",
    "How did Robespierre create meiosis?",
    "Why did chromosomes limit royal power?",
    "How did DNA command Roman legions?",
    "Why did meiosis overthrow the Roman Republic?",
    "How did photosynthesis sign medieval English law?",
    "Why did the Magna Carta divide chromosomes?",
    "How did Roman senators perform photosynthesis?",
    "Why did DNA lead French revolutionary armies?",
    "How did mitosis weaken King John?",
    "Why did Robespierre produce haploid cells?",
    "How did Roman cohorts replicate DNA?",
    "Why did photosynthesis organize the Roman Senate?",
]

for question in NEGATIVE_QUESTIONS:
    add_case(
        "negative",
        question,
        "system",
        False,
        [
            "couldn't find enough reliable evidence",
        ],
    )


# ==========================================================
# VERIFY TEST COUNT
# ==========================================================

if len(
    TESTS
) != EXPECTED_TEST_COUNT:
    raise RuntimeError(
        "Evaluation V3 test count mismatch: "
        f"expected {EXPECTED_TEST_COUNT}, "
        f"got {len(TESTS)}."
    )


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

        "canonical_question":
            result.get(
                "canonical_question"
            ),

        "premise_validation":
            result.get(
                "premise_validation"
            ),

        "retrieval_plan":
            result.get(
                "retrieval_plan"
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
# MAIN
# ==========================================================

def main():
    print(
        "\n"
        + "=" * 76
    )

    print(
        "AI PROJECT - EVALUATION SUITE V3"
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

    # ======================================================
    # EXECUTION
    # ======================================================

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

    # ======================================================
    # COUNTS
    # ======================================================

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

    # ======================================================
    # SUPPORT METRICS
    # ======================================================

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

    # ======================================================
    # CATEGORY RESULTS
    # ======================================================

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

    # ======================================================
    # CORE METRICS
    # ======================================================

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

    # ======================================================
    # TARGET STATUS
    # ======================================================

    target_checks = {
        "semantic":
            semantic_accuracy
            >= TARGET_SEMANTIC_ACCURACY,

        "type":
            type_accuracy
            >= TARGET_TYPE_ACCURACY,

        "support":
            support_accuracy
            >= TARGET_SUPPORT_ACCURACY,

        "false_premise":
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
        "PASS"
        if target_checks[
            "semantic"
        ]
        else "FAIL",
    )

    print(
        "Answer type >= 95%:        ",
        "PASS"
        if target_checks[
            "type"
        ]
        else "FAIL",
    )

    print(
        "Support state >= 95%:      ",
        "PASS"
        if target_checks[
            "support"
        ]
        else "FAIL",
    )

    print(
        "False-premise >= 95%:      ",
        "PASS"
        if target_checks[
            "false_premise"
        ]
        else "FAIL",
    )

    print(
        "Supported acceptance >=95%:",
        "PASS"
        if target_checks[
            "supported_acceptance"
        ]
        else "FAIL",
    )

    # ======================================================
    # FAILURE ANALYSIS
    # ======================================================

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
                "Canonical question:",
                result[
                    "canonical_question"
                ],
            )

            print(
                "Premise validation:",
                result[
                    "premise_validation"
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

    # ======================================================
    # FINAL STATUS
    # ======================================================

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
            "EVALUATION V3 STATUS: PASS"
        )

    elif all_targets_pass:
        print(
            "EVALUATION V3 STATUS: "
            "TARGETS PASS, "
            "BUT CASE FAILURES EXIST"
        )

    else:
        print(
            "EVALUATION V3 STATUS: FAIL"
        )

    print(
        "=" * 76
    )


if __name__ == "__main__":
    main()