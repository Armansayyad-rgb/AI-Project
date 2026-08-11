import subprocess
import sys


TESTS = [
    {
        "name": "extractor_missing_fact",
        "question": "When was Albert Einstein born?",
        "must_contain": [
            "couldn't find enough reliable evidence",
        ],
    },
    {
        "name": "causal",
        "question": "Why did the Roman Empire decline?",
        "must_contain": [
            "Causal synthesizer:",
        ],
    },
    {
        "name": "change",
        "question": "How did the Roman Empire change over time?",
        "must_contain": [
            "Change synthesizer:",
        ],
    },
    {
        "name": "effect",
        "question": "What were the effects of the fall of the Roman Empire?",
        "must_contain": [
            "Effect synthesizer:",
        ],
    },
    {
        "name": "entity_list",
        "question": "Who were the main leaders of the French Revolution?",
        "must_contain": [
            "Entity-list synthesizer:",
            "Maximilien Robespierre",
            "Georges Danton",
        ],
    },
    {
        "name": "roman_structure",
        "question": "How was the Roman army organized?",
        "must_contain": [
            "Structure synthesizer:",
            "cohort",
            "centuries",
        ],
    },
    {
        "name": "dna_structure",
        "question": "Explain the structure of DNA.",
        "must_contain": [
            "Structure synthesizer:",
            "double-stranded",
            "Adenine",
            "thymine",
        ],
    },
    {
        "name": "photosynthesis_summary",
        "question": "Explain how photosynthesis works.",
        "must_contain": [
            "Summary synthesizer:",
            "sunlight",
            "carbon dioxide",
            "oxygen",
        ],
    },
    {
        "name": "magna_carta_summary",
        "question": "What is the significance of the Magna Carta?",
        "must_contain": [
            "Summary synthesizer:",
            "limited royal power",
        ],
    },
    {
        "name": "comparison",
        "question": "What are the differences between mitosis and meiosis?",
        "must_contain": [
            "Comparison synthesizer:",
            "Mitosis",
            "Meiosis",
            "haploid",
        ],
    },
]


def run_test(test):
    process = subprocess.run(
        [
            sys.executable,
            "rag_chat_v2.py",
        ],
        input=(
            test["question"]
            + "\nquit\n"
        ),
        text=True,
        capture_output=True,
    )

    output = (
        process.stdout
        + process.stderr
    )

    missing = []

    for expected in test[
        "must_contain"
    ]:
        if (
            expected.lower()
            not in output.lower()
        ):
            missing.append(
                expected
            )

    passed = (
        process.returncode == 0
        and not missing
    )

    return {
        "passed": passed,
        "missing": missing,
        "output": output,
        "returncode":
            process.returncode,
    }


def main():
    print(
        "\nRunning regression tests...\n"
    )

    print(
        "Python interpreter:",
        sys.executable,
    )

    print()

    passed_count = 0
    failed_count = 0
    failures = []

    for test in TESTS:
        print(
            f"Testing: {test['name']}"
        )

        result = run_test(
            test
        )

        if result[
            "passed"
        ]:
            passed_count += 1

            print(
                "PASS\n"
            )

        else:
            failed_count += 1

            print(
                "FAIL"
            )

            if result[
                "missing"
            ]:
                print(
                    "Missing:",
                    ", ".join(
                        result[
                            "missing"
                        ]
                    ),
                )

            print()

            failures.append(
                (
                    test,
                    result,
                )
            )

    print(
        "=" * 60
    )

    print(
        f"Passed: {passed_count}"
    )

    print(
        f"Failed: {failed_count}"
    )

    print(
        f"Total:  {len(TESTS)}"
    )

    print(
        "=" * 60
    )

    if failures:
        print(
            "\n--- FAILURE DETAILS ---"
        )

        for test, result in failures:
            print(
                "\n"
                + "=" * 60
            )

            print(
                "Test:",
                test[
                    "name"
                ],
            )

            print(
                "Question:",
                test[
                    "question"
                ],
            )

            print(
                "Return code:",
                result[
                    "returncode"
                ],
            )

            print(
                "Missing:",
                result[
                    "missing"
                ],
            )

            print(
                "\n--- OUTPUT ---\n"
            )

            print(
                result[
                    "output"
                ]
            )


if __name__ == "__main__":
    main()