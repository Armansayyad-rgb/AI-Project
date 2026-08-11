# -*- coding: utf-8 -*-
"""
Unit tests for extract_asserted_relation() in rag_chat_v2.py.

The function detects questions that explicitly assert a
relationship between two concepts.  These tests pin down the
expected behavior for both TRUE positives (false-premise
questions that SHOULD be detected) and TRUE negatives
(ordinary single-subject questions that should NOT trigger
the asserted-relation gate).
"""

import os
import sys

# Make sure we can import the module under test from
# the same directory regardless of where this script is
# invoked from.
THIS_DIR = os.path.dirname(
    os.path.abspath(__file__)
)
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from rag_chat_v2 import (
    extract_asserted_relation,
)


# ==================================================
# TEST CASES
# ==================================================
#
# Each case is:
#     (question, expected_relation, expected_source, expected_target)
#
# Use None for the relation (and source/target) when the
# question is an ordinary single-subject question that
# must NOT trigger the asserted-relation detector.

TEST_CASES = [
    # --------------------------------------------------
    # Original cases from the prompt
    # --------------------------------------------------

    # True positive - "invent" relation
    (
        "Why did Albert Einstein invent the telephone?",
        "invent",
        "Albert Einstein",
        "the telephone",
    ),

    # True positive - "create" relation
    (
        "How did DNA create the Roman Empire?",
        "create",
        "DNA",
        "the Roman Empire",
    ),

    # True positive - "organize" relation
    (
        "Explain how photosynthesis organized the Roman army.",
        "organize",
        "photosynthesis",
        "the Roman army",
    ),

    # True negative - ordinary causal question, no cross-concept relation
    (
        "Why did the Roman Empire decline?",
        None,
        None,
        None,
    ),

    # True negative - ordinary structural question
    (
        "How was the Roman army organized?",
        None,
        None,
        None,
    ),

    # --------------------------------------------------
    # Discover pattern (mapped to "invent" relation in code)
    # --------------------------------------------------

    (
        "Why did Isaac Newton discover calculus?",
        "invent",
        "Isaac Newton",
        "calculus",
    ),

    # --------------------------------------------------
    # Build pattern - NOT supported by the detector.
    # The function only recognizes create/produce/generate/form
    # under the "create" relation.  "build" does not match.
    # --------------------------------------------------

    (
        "Why did X build Y?",
        None,
        None,
        None,
    ),

    # --------------------------------------------------
    # Destroy pattern - NOT supported by the detector.
    # There is no "destroy" pattern in the rules.
    # --------------------------------------------------

    (
        "How did X destroy Y?",
        None,
        None,
        None,
    ),

    # --------------------------------------------------
    # Become pattern - NOT supported by the detector.
    # There is no "become" pattern in the rules.
    # --------------------------------------------------

    (
        "Explain how X became Y",
        None,
        None,
        None,
    ),

    # --------------------------------------------------
    # Additional patterns to broaden coverage
    # --------------------------------------------------

    # Develop pattern (mapped to "invent" relation)
    (
        "Why did Alexander Graham Bell develop the radio?",
        "invent",
        "Alexander Graham Bell",
        "the radio",
    ),

    # Explain why ... invented ...
    (
        "Explain why Marie Curie invented radium therapy.",
        "invent",
        "Marie Curie",
        "radium therapy",
    ),

    # Describe how ... caused ...
    (
        "Explain how the moon caused the tides.",
        "cause",
        "the moon",
        "the tides",
    ),

    # Describe X as Y (adversarial identity claim)
    (
        "Describe DNA as a political institution of Rome.",
        "describe_as",
        "DNA",
        "a political institution of Rome",
    ),

    # Why did X split Y
    (
        "Why did Rome split the empire?",
        "split",
        "Rome",
        "the empire",
    ),

    # How did X govern Y
    (
        "How did Caesar govern Gaul?",
        "govern",
        "Caesar",
        "Gaul",
    ),
]


def test_extract_asserted_relation():
    """Run all test cases and report pass/fail."""
    passed = 0
    total = len(TEST_CASES)

    for (
        idx,
        (
            question,
            expected_relation,
            expected_source,
            expected_target,
        ),
    ) in enumerate(
        TEST_CASES,
        start=1,
    ):
        result = extract_asserted_relation(
            question
        )

        # ---- determine actual values ----
        if result is None:
            actual_relation = None
            actual_source = None
            actual_target = None
        else:
            actual_relation = result.get(
                "relation"
            )
            actual_source = result.get(
                "source"
            )
            actual_target = result.get(
                "target"
            )

        # ---- compare ----
        ok = (
            actual_relation
            == expected_relation
            and actual_source
            == expected_source
            and actual_target
            == expected_target
        )

        status = "PASS" if ok else "FAIL"
        print(
            f"[{status}] Case {idx}: "
            f"{question!r}"
        )

        if not ok:
            print(
                "  expected: "
                f"relation={expected_relation!r}, "
                f"source={expected_source!r}, "
                f"target={expected_target!r}"
            )
            print(
                "  actual:   "
                f"relation={actual_relation!r}, "
                f"source={actual_source!r}, "
                f"target={actual_target!r}"
            )

        if ok:
            passed += 1

    print()
    print(f"Passed: {passed}/{total}")

    return passed, total


if __name__ == "__main__":
    test_extract_asserted_relation()
