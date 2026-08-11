import re


# --------------------------------------------------
# Configuration
# --------------------------------------------------

MIN_TERM_COVERAGE = 0.55
MIN_SUPPORTING_SENTENCES = 1
MIN_BEST_SENTENCE_OVERLAP = 0.65
MIN_SCORE = 0.62


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "by",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",

    # Conversational / instruction words
    "about",
    "tell",
    "me",
    "explain",
    "describe",
    "discuss",
    "please",
}


# --------------------------------------------------
# Relation vocabulary
# --------------------------------------------------

RELATION_GROUPS = {
    "causal": {
        "cause",
        "caused",
        "causes",
        "because",
        "lead",
        "led",
        "leading",
        "result",
        "resulted",
        "results",
        "due",
    },

    "change": {
        "change",
        "changed",
        "changes",
        "evolve",
        "evolved",
        "develop",
        "developed",
        "transform",
        "transformed",
    },

    "comparison": {
        "compare",
        "comparison",
        "different",
        "difference",
        "differences",
        "versus",
    },
}


# --------------------------------------------------
# Text helpers
# --------------------------------------------------

def tokenize(text):
    return re.findall(
        r"[a-z0-9']+",
        text.lower(),
    )


def content_terms(text):
    return {
        word
        for word in tokenize(
            text
        )
        if (
            word not in STOPWORDS
            and len(word) >= 3
        )
    }


def split_sentences(text):
    return [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )
        if sentence.strip()
    ]


# --------------------------------------------------
# Retrieval score normalization
# --------------------------------------------------

def normalized_retrieval_score(
    retrieval_score,
):
    if retrieval_score <= 0:
        return 0.0

    return min(
        1.0,
        retrieval_score / 60.0,
    )


# --------------------------------------------------
# Relation detection
# --------------------------------------------------

def detect_required_relation(
    question,
):
    question_terms = set(
        tokenize(
            question
        )
    )

    for (
        relation_name,
        relation_terms,
    ) in RELATION_GROUPS.items():

        if (
            question_terms
            & relation_terms
        ):
            return relation_name

    return None


def sentence_has_relation(
    sentence,
    relation_name,
):
    if relation_name is None:
        return True

    terms = set(
        tokenize(
            sentence
        )
    )

    relation_terms = (
        RELATION_GROUPS.get(
            relation_name,
            set(),
        )
    )

    return bool(
        terms
        & relation_terms
    )


# --------------------------------------------------
# Sentence support
# --------------------------------------------------

def sentence_overlap(
    sentence,
    question_terms,
):
    if not question_terms:
        return 0.0

    sentence_terms = content_terms(
        sentence
    )

    overlap = len(
        question_terms
        & sentence_terms
    )

    return (
        overlap
        / len(question_terms)
    )


def best_sentence_support(
    question_terms,
    sentences,
):
    best_overlap = 0.0
    best_sentence = ""

    for sentence in sentences:
        overlap = sentence_overlap(
            sentence,
            question_terms,
        )

        if overlap > best_overlap:
            best_overlap = overlap
            best_sentence = sentence

    return (
        best_overlap,
        best_sentence,
    )


# --------------------------------------------------
# Relation support
# --------------------------------------------------

def relation_support_found(
    question_terms,
    sentences,
    required_relation,
):
    if required_relation is None:
        return True

    for sentence in sentences:

        overlap = sentence_overlap(
            sentence,
            question_terms,
        )

        if (
            overlap >= 0.50
            and sentence_has_relation(
                sentence,
                required_relation,
            )
        ):
            return True

    return False


# --------------------------------------------------
# Main confidence function
# --------------------------------------------------

def reasoning_support_confidence(
    question,
    context,
    retrieval_score=0.0,
):
    question_terms = content_terms(
        question
    )

    sentences = split_sentences(
        context
    )

    retrieval_component = (
        normalized_retrieval_score(
            retrieval_score
        )
    )

    if not question_terms:
        return {
            "score":
                0.0,

            "sufficient":
                False,

            "term_coverage":
                0.0,

            "supporting_sentences":
                0,

            "best_sentence_overlap":
                0.0,

            "retrieval_component":
                retrieval_component,

            "relation":
                None,

            "relation_supported":
                False,

            "matched_terms":
                [],

            "question_terms":
                [],

            "best_sentence":
                "",
        }

    context_terms = content_terms(
        context
    )

    matched_terms = (
        question_terms
        & context_terms
    )

    term_coverage = (
        len(matched_terms)
        / len(question_terms)
    )

    (
        best_sentence_overlap,
        best_sentence,
    ) = best_sentence_support(
        question_terms,
        sentences,
    )

    supporting_sentences = sum(
        1
        for sentence in sentences
        if sentence_overlap(
            sentence,
            question_terms,
        ) >= 0.50
    )

    required_relation = (
        detect_required_relation(
            question
        )
    )

    relation_supported = (
        relation_support_found(
            question_terms,
            sentences,
            required_relation,
        )
    )

    # ------------------------------------------
    # Combined score
    # ------------------------------------------

    score = (
        0.45 * term_coverage
        + 0.40 * best_sentence_overlap
        + 0.15 * retrieval_component
    )

    # ------------------------------------------
    # Minimum matched terms
    # ------------------------------------------

    if len(question_terms) >= 4:
        enough_matched_terms = (
            len(matched_terms) >= 3
        )

    elif len(question_terms) >= 2:
        enough_matched_terms = (
            len(matched_terms) >= 2
        )

    else:
        enough_matched_terms = (
            len(matched_terms) >= 1
        )

    # ------------------------------------------
    # Final gate
    # ------------------------------------------

    sufficient = (
        enough_matched_terms
        and term_coverage
        >= MIN_TERM_COVERAGE
        and supporting_sentences
        >= MIN_SUPPORTING_SENTENCES
        and best_sentence_overlap
        >= MIN_BEST_SENTENCE_OVERLAP
        and relation_supported
        and score
        >= MIN_SCORE
    )

    return {
        "score":
            score,

        "sufficient":
            sufficient,

        "term_coverage":
            term_coverage,

        "supporting_sentences":
            supporting_sentences,

        "best_sentence_overlap":
            best_sentence_overlap,

        "retrieval_component":
            retrieval_component,

        "relation":
            required_relation,

        "relation_supported":
            relation_supported,

        "matched_terms":
            sorted(
                matched_terms
            ),

        "question_terms":
            sorted(
                question_terms
            ),

        "best_sentence":
            best_sentence,
    }


# --------------------------------------------------
# Standalone tests
# --------------------------------------------------

if __name__ == "__main__":

    tests = [
        # ------------------------------------------
        # Should PASS
        # ------------------------------------------

        (
            "Tell me about the Roman Empire.",
            (
                "The Roman Empire controlled "
                "large parts of Europe, North "
                "Africa, and western Asia. "
                "Roman institutions developed "
                "over many centuries."
            ),
            48.0,
            True,
        ),

        # ------------------------------------------
        # Should FAIL:
        # both topics exist, but no relationship
        # connects DNA to the Roman Empire.
        # ------------------------------------------

        (
            "How did DNA lead to "
            "the Roman Empire?",
            (
                "DNA consists of nucleotide "
                "sequences and is organized "
                "into chromosomes. "
                "The Roman Empire developed "
                "from the Roman Republic."
            ),
            45.0,
            False,
        ),

        # ------------------------------------------
        # Should FAIL:
        # both subjects occur independently.
        # ------------------------------------------

        (
            "Why did the Magna Carta "
            "cause photosynthesis?",
            (
                "The Magna Carta limited royal "
                "power in medieval England. "
                "Photosynthesis converts water "
                "and carbon dioxide into sugars "
                "using sunlight."
            ),
            46.0,
            False,
        ),

        # ------------------------------------------
        # Should PASS:
        # actual causal relation exists.
        # ------------------------------------------

        (
            "What caused the decline "
            "of the population?",
            (
                "The population declined because "
                "disease and food shortages caused "
                "a sharp increase in mortality."
            ),
            50.0,
            True,
        ),
    ]

    passed = 0

    for (
        question,
        context,
        retrieval_score,
        expected,
    ) in tests:

        result = (
            reasoning_support_confidence(
                question,
                context,
                retrieval_score,
            )
        )

        actual = result[
            "sufficient"
        ]

        test_passed = (
            actual == expected
        )

        if test_passed:
            passed += 1

        print()

        print(
            "=" * 60
        )

        print(
            "Question:",
            question,
        )

        print(
            "Expected:",
            expected,
        )

        print(
            "Actual:",
            actual,
        )

        print(
            "Test:",
            (
                "PASS"
                if test_passed
                else "FAIL"
            ),
        )

        print(
            "Score:",
            f"{result['score']:.3f}",
        )

        print(
            "Coverage:",
            f"{result['term_coverage']:.3f}",
        )

        print(
            "Best sentence overlap:",
            f"{result['best_sentence_overlap']:.3f}",
        )

        print(
            "Relation:",
            result[
                "relation"
            ],
        )

        print(
            "Relation supported:",
            result[
                "relation_supported"
            ],
        )

        print(
            "Matched terms:",
            result[
                "matched_terms"
            ],
        )

        print(
            "Best sentence:",
            result[
                "best_sentence"
            ],
        )

    print()

    print(
        "=" * 60
    )

    print(
        f"Passed: {passed}/{len(tests)}"
    )

    print(
        "=" * 60
    )