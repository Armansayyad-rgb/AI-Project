import re


MIN_SENTENCES = 2
MIN_SCORE = 0.55


# --------------------------------------------------
# Text helpers
# --------------------------------------------------

def split_sentences(text):
    return [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )
        if sentence.strip()
    ]


def normalize(text):
    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


# --------------------------------------------------
# Entity helpers
# --------------------------------------------------

def entity_from_side(side_label):
    text = side_label.strip()

    patterns = [
        r"(?:the )?fall of (.+)$",
        r"(?:the )?decline of (.+)$",
        r"(?:the )?collapse of (.+)$",
        r"(?:the )?end of (.+)$",
    ]

    for pattern in patterns:
        match = re.match(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return (
                match.group(1)
                .strip()
            )

    return text


def entity_terms(entity):
    entity = normalize(
        entity
    )

    terms = [
        entity
    ]

    words = entity.split()

    if (
        len(words) >= 2
        and words[-1] in {
            "empire",
            "kingdom",
            "republic",
            "state",
        }
    ):
        shorter = " ".join(
            words[:-1]
        ).strip()

        if shorter:
            terms.append(
                shorter
            )

    return terms


def sentence_mentions_entity(
    sentence,
    entity,
):
    s = normalize(
        sentence
    )

    return any(
        term in s
        for term in entity_terms(
            entity
        )
    )


# --------------------------------------------------
# Comparison mode detection
# --------------------------------------------------

def detect_mode(side_label):
    label = normalize(
        side_label
    )

    if any(
        marker in label
        for marker in [
            "fall of",
            "decline of",
            "collapse of",
            "end of",
        ]
    ):
        return "fall"

    return "general"


# --------------------------------------------------
# Fall relation markers
# --------------------------------------------------

def relation_markers(side_label):
    label = normalize(
        side_label
    )

    if any(
        word in label
        for word in [
            "fall",
            "decline",
            "collapse",
            "end",
        ]
    ):
        return [
            "fall",
            "fell",
            "decline",
            "declined",
            "collapse",
            "collapsed",
            "dissolution",
            "dissolved",
            "ended",
            "end of",
            "defeat",
            "defeated",
            "overrun",
            "invasion",
            "invading",
            "revolt",
            "lost territory",
            "territorial loss",
        ]

    return []


# --------------------------------------------------
# General evidence markers
# --------------------------------------------------

GENERAL_EVIDENCE_MARKERS = [
    "division",
    "divides",
    "produces",
    "forms",
    "contains",
    "consists",
    "structure",
    "function",
    "process",
    "chromosome",
    "chromosomes",
    "daughter cells",
    "haploid",
    "diploid",
    "gamete",
    "gametes",
    "homologous",
    "crossing over",
    "recombination",
    "genetic",
    "identical",
    "different",
    "prophase",
    "metaphase",
    "anaphase",
    "telophase",
]


def has_general_evidence(sentence):
    lower = normalize(
        sentence
    )

    return any(
        marker in lower
        for marker in GENERAL_EVIDENCE_MARKERS
    )


# --------------------------------------------------
# Side scoring
# --------------------------------------------------

def score_side(
    side_label,
    context,
):
    entity = entity_from_side(
        side_label
    )

    mode = detect_mode(
        side_label
    )

    sentences = split_sentences(
        context
    )

    if not sentences:
        return {
            "score": 0.0,
            "sufficient": False,
            "entity_hits": 0,
            "relation_hits": 0,
            "evidence_hits": 0,
            "sentence_count": 0,
            "mode": mode,
        }

    entity_hits = 0
    relation_hits = 0
    evidence_hits = 0

    markers = relation_markers(
        side_label
    )

    for sentence in sentences:
        lower = normalize(
            sentence
        )

        has_entity = (
            sentence_mentions_entity(
                sentence,
                entity,
            )
        )

        if has_entity:
            entity_hits += 1

        # ------------------------------------------
        # Fall comparison
        # ------------------------------------------

        if mode == "fall":

            if (
                has_entity
                and any(
                    marker in lower
                    for marker in markers
                )
            ):
                relation_hits += 1

        # ------------------------------------------
        # General comparison
        # ------------------------------------------

        else:

            if (
                has_entity
                and has_general_evidence(
                    sentence
                )
            ):
                evidence_hits += 1

    sentence_count = len(
        sentences
    )

    # ------------------------------------------
    # Fall-mode score
    # ------------------------------------------

    if mode == "fall":

        # One direct entity hit is enough for
        # full entity coverage.
        entity_component = min(
            1.0,
            float(entity_hits),
        )

        # One direct fall/decline relation hit
        # is enough for full relation coverage.
        relation_component = min(
            1.0,
            float(relation_hits),
        )

        coverage_component = min(
            1.0,
            sentence_count / 3.0,
        )

        score = (
            0.45 * entity_component
            + 0.40 * relation_component
            + 0.15 * coverage_component
        )

        sufficient = (
            sentence_count >= 1
            and entity_hits >= 1
            and relation_hits >= 1
            and score >= MIN_SCORE
        )

    # ------------------------------------------
    # General-mode score
    # ------------------------------------------

    else:

        # One explicit entity hit is enough.
        entity_component = min(
            1.0,
            float(entity_hits),
        )

        # One strong descriptive evidence hit
        # is enough.
        evidence_component = min(
            1.0,
            float(evidence_hits),
        )

        coverage_component = min(
            1.0,
            sentence_count / 3.0,
        )

        score = (
            0.50 * entity_component
            + 0.35 * evidence_component
            + 0.15 * coverage_component
        )

        sufficient = (
            sentence_count >= 1
            and entity_hits >= 1
            and evidence_hits >= 1
            and score >= MIN_SCORE
        )

    return {
        "score":
            score,

        "sufficient":
            sufficient,

        "entity_hits":
            entity_hits,

        "relation_hits":
            relation_hits,

        "evidence_hits":
            evidence_hits,

        "sentence_count":
            sentence_count,

        "mode":
            mode,
    }


# --------------------------------------------------
# Comparison scoring
# --------------------------------------------------

def score_comparison(
    result,
):
    if result is None:
        return {
            "sufficient":
                False,

            "left":
                None,

            "right":
                None,
        }

    plan = result[
        "plan"
    ]

    left = score_side(
        plan[
            "left_entity"
        ],
        result[
            "left_context"
        ],
    )

    right = score_side(
        plan[
            "right_entity"
        ],
        result[
            "right_context"
        ],
    )

    return {
        "sufficient": (
            left[
                "sufficient"
            ]
            and right[
                "sufficient"
            ]
        ),

        "left":
            left,

        "right":
            right,
    }


# --------------------------------------------------
# Standalone tests
# --------------------------------------------------

if __name__ == "__main__":

    print(
        "\n--- FALL TEST ---"
    )

    roman_context = (
        "Many theories have been advanced for the decline "
        "of the Roman Empire. "
        "The Roman Empire fell after being overrun by "
        "non-Roman peoples and Germanic troops."
    )

    ottoman_context = (
        "The Ottoman Empire declined because of military "
        "defeats and territorial losses."
    )

    left = score_side(
        "the fall of the Roman Empire",
        roman_context,
    )

    right = score_side(
        "the fall of the Ottoman Empire",
        ottoman_context,
    )

    print(
        "Roman:",
        left,
    )

    print(
        "Ottoman:",
        right,
    )

    print(
        "Comparison sufficient:",
        (
            left["sufficient"]
            and right["sufficient"]
        ),
    )

    print(
        "\n--- MITOSIS / MEIOSIS TEST ---"
    )

    mitosis_context = (
        "In closed mitosis, the daughter chromosomes "
        "migrate to opposite poles of the nucleus, "
        "which then divides in two. "
        "In most cells, prophase is an early stage "
        "of mitosis."
    )

    meiosis_context = (
        "Meiosis is a specialized form of cell division "
        "that produces haploid gametes."
    )

    left = score_side(
        "mitosis",
        mitosis_context,
    )

    right = score_side(
        "meiosis",
        meiosis_context,
    )

    print(
        "Mitosis:",
        left,
    )

    print(
        "Meiosis:",
        right,
    )

    print(
        "Comparison sufficient:",
        (
            left["sufficient"]
            and right["sufficient"]
        ),
    )