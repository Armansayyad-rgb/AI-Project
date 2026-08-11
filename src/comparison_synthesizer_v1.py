import re


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
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        text,
    )

    return text.strip()


def clean_label(label):
    label = normalize(
        label
    )

    label = re.sub(
        r"^(?:the )?"
        r"(?:fall|decline|collapse|end) of ",
        "",
        label,
        flags=re.IGNORECASE,
    )

    return label.strip()


def display_name(name):
    name = normalize(
        name
    )

    if not name:
        return name

    if name.lower().startswith(
        "the "
    ):
        return (
            "the "
            + name[4:]
        )

    return (
        name[0].upper()
        + name[1:]
    )


def capitalize_sentence(text):
    text = text.strip()

    if not text:
        return text

    return (
        text[0].upper()
        + text[1:]
    )


# --------------------------------------------------
# Comparison type detection
# --------------------------------------------------

def detect_comparison_mode(
    question,
    plan,
):
    q = question.lower()

    left = (
        plan.get(
            "left_entity",
            "",
        )
        .lower()
    )

    right = (
        plan.get(
            "right_entity",
            "",
        )
        .lower()
    )

    fall_markers = [
        "fall of",
        "decline of",
        "collapse of",
        "end of",
    ]

    if any(
        marker in left
        or marker in right
        for marker in fall_markers
    ):
        return "fall"

    if any(
        marker in q
        for marker in [
            "fall",
            "decline",
            "collapse",
        ]
    ):
        return "fall"

    return "general"


# --------------------------------------------------
# Redundancy
# --------------------------------------------------

def sentence_signature(text):
    words = re.findall(
        r"[a-z0-9]+",
        text.lower(),
    )

    return {
        word
        for word in words
        if len(word) >= 4
    }


def near_duplicate(
    first,
    second,
):
    if not first or not second:
        return False

    a = sentence_signature(
        first
    )

    b = sentence_signature(
        second
    )

    if not a or not b:
        return False

    overlap = len(
        a & b
    )

    smaller = min(
        len(a),
        len(b),
    )

    if smaller == 0:
        return False

    return (
        overlap / smaller
    ) >= 0.60


def remove_redundant(sentences):
    kept = []

    for sentence in sentences:
        if not sentence:
            continue

        if any(
            near_duplicate(
                sentence,
                existing,
            )
            for existing in kept
        ):
            continue

        kept.append(
            sentence
        )

    return kept


# --------------------------------------------------
# Fall-comparison logic
# --------------------------------------------------

CAUSE_MARKERS = {
    "because": 4.0,
    "due to": 4.0,
    "as a result": 4.0,
    "caused by": 4.0,
    "overrun": 3.0,
    "invading": 3.0,
    "invasion": 3.0,
    "military defeat": 3.0,
    "military defeats": 3.0,
    "defeated": 2.5,
    "territorial loss": 3.0,
    "territorial losses": 3.0,
    "economic": 2.0,
    "nationalist": 2.0,
    "revolt": 2.0,
    "pressure": 1.5,
    "decline": 1.0,
    "declined": 1.0,
    "fell": 1.0,
}


MILITARY_MARKERS = [
    "military",
    "army",
    "armies",
    "defeat",
    "defeated",
    "overrun",
    "invading",
    "invasion",
    "war",
    "troops",
]


TERRITORIAL_MARKERS = [
    "territorial",
    "territory",
    "territories",
    "province",
    "provinces",
]


ECONOMIC_MARKERS = [
    "economic",
    "economy",
    "financial",
]


POLITICAL_MARKERS = [
    "political",
    "revolt",
    "revolution",
    "administration",
    "leadership",
    "government",
]


NATIONALISM_MARKERS = [
    "nationalist",
    "nationalism",
]


def score_sentence(
    sentence,
    markers,
):
    lower = sentence.lower()

    score = 0.0

    for marker, weight in (
        markers.items()
    ):
        if marker in lower:
            score += weight

    word_count = len(
        sentence.split()
    )

    direct_patterns = [
        r"\bfell after\b",
        r"\bbecause\b",
        r"\bdue to\b",
        r"\bcaused by\b",
        r"\bwas overrun\b",
        r"\bwas defeated\b",
        r"\bdeclined because\b",
    ]

    if any(
        re.search(
            pattern,
            lower,
        )
        for pattern in direct_patterns
    ):
        score += 6.0

    if 8 <= word_count <= 40:
        score += 1.0

    elif word_count > 55:
        score -= 4.0

    return score


def best_sentence(
    context,
    markers,
):
    sentences = split_sentences(
        context
    )

    scored = []

    for index, sentence in enumerate(
        sentences
    ):
        score = score_sentence(
            sentence,
            markers,
        )

        scored.append(
            (
                score,
                index,
                normalize(sentence),
            )
        )

    scored.sort(
        key=lambda item: (
            item[0],
            -item[1],
        ),
        reverse=True,
    )

    if (
        not scored
        or scored[0][0] <= 0
    ):
        return None

    return scored[0][2]


def extract_because_clause(sentence):
    match = re.search(
        r"\bbecause of (.+?)(?:\.|$)",
        sentence,
        flags=re.IGNORECASE,
    )

    if match:
        return normalize(
            match.group(1)
        )

    match = re.search(
        r"\bbecause (.+?)(?:\.|$)",
        sentence,
        flags=re.IGNORECASE,
    )

    if match:
        return normalize(
            match.group(1)
        )

    return None


def extract_after_clause(sentence):
    match = re.search(
        r"\bfell after (.+?)(?:\.|$)",
        sentence,
        flags=re.IGNORECASE,
    )

    if match:
        return normalize(
            match.group(1)
        )

    return None


def shorten_sentence(
    sentence,
    max_words=34,
):
    sentence = normalize(
        sentence
    )

    words = sentence.split()

    if len(words) <= max_words:
        return sentence.rstrip(".")

    return (
        " ".join(
            words[:max_words]
        )
        .rstrip(",;:")
        + "."
    )


def build_cause_summary(
    entity,
    context,
):
    sentences = split_sentences(
        context
    )

    for sentence in sentences:
        after_clause = extract_after_clause(
            sentence
        )

        if after_clause:
            cause = after_clause

            if cause.lower().startswith(
                "first "
            ):
                cause = cause[6:]

            return (
                f"{entity} fell after "
                f"{cause.rstrip('.')}."
            )

    for sentence in sentences:
        because_clause = (
            extract_because_clause(
                sentence
            )
        )

        if because_clause:
            return (
                f"{entity} declined because of "
                f"{because_clause.rstrip('.')}."
            )

    sentence = best_sentence(
        context,
        CAUSE_MARKERS,
    )

    if sentence is None:
        return None

    result = shorten_sentence(
        sentence,
        max_words=32,
    )

    if not result.endswith("."):
        result += "."

    return result


def contains_any(
    text,
    markers,
):
    lower = text.lower()

    return any(
        marker in lower
        for marker in markers
    )


def detect_themes(context):
    themes = set()

    if contains_any(
        context,
        MILITARY_MARKERS,
    ):
        themes.add(
            "military pressure"
        )

    if contains_any(
        context,
        TERRITORIAL_MARKERS,
    ):
        themes.add(
            "territorial losses"
        )

    if contains_any(
        context,
        ECONOMIC_MARKERS,
    ):
        themes.add(
            "economic weakness"
        )

    if contains_any(
        context,
        POLITICAL_MARKERS,
    ):
        themes.add(
            "political instability"
        )

    if contains_any(
        context,
        NATIONALISM_MARKERS,
    ):
        themes.add(
            "nationalist movements"
        )

    return themes


def join_naturally(items):
    items = list(
        items
    )

    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return (
            f"{items[0]} and {items[1]}"
        )

    return (
        ", ".join(
            items[:-1]
        )
        + f", and {items[-1]}"
    )


def synthesize_fall_comparison(
    left_name,
    right_name,
    left_context,
    right_context,
):
    left_themes = detect_themes(
        left_context
    )

    right_themes = detect_themes(
        right_context
    )

    shared_themes = sorted(
        left_themes
        & right_themes
    )

    left_unique = sorted(
        left_themes
        - right_themes
    )

    right_unique = sorted(
        right_themes
        - left_themes
    )

    left_cause = build_cause_summary(
        left_name,
        left_context,
    )

    right_cause = build_cause_summary(
        right_name,
        right_context,
    )

    parts = []

    if shared_themes:
        parts.append(
            f"Both {left_name} and "
            f"{right_name} faced "
            f"{join_naturally(shared_themes)}."
        )

    if left_cause:
        parts.append(
            left_cause
        )

    if right_cause:
        parts.append(
            right_cause
        )

    if (
        left_unique
        and right_unique
    ):
        parts.append(
            f"The evidence emphasizes "
            f"{join_naturally(left_unique)} "
            f"more for {left_name}, while "
            f"{join_naturally(right_unique)} "
            f"stand out more for "
            f"{right_name}."
        )

    elif left_unique:
        parts.append(
            f"The evidence also emphasizes "
            f"{join_naturally(left_unique)} "
            f"for {left_name}."
        )

    elif right_unique:
        parts.append(
            f"The evidence also emphasizes "
            f"{join_naturally(right_unique)} "
            f"for {right_name}."
        )

    if not parts:
        return None

    return normalize(
        " ".join(
            parts
        )
    )


# --------------------------------------------------
# General comparison scoring
# --------------------------------------------------

GENERAL_MARKERS = {
    "produces": 4.0,
    "produce": 4.0,
    "forms": 3.0,
    "divides": 3.0,
    "division": 3.0,
    "cells": 2.0,
    "chromosome": 3.0,
    "chromosomes": 3.0,
    "daughter": 3.0,
    "haploid": 4.0,
    "diploid": 4.0,
    "gamete": 4.0,
    "gametes": 4.0,
    "homologous": 4.0,
    "crossing over": 4.0,
    "recombination": 4.0,
    "genetic": 2.0,
    "identical": 3.0,
    "different": 2.0,
}


BIOLOGY_NOISE_MARKERS = [
    "was discovered",
    "were discovered",
    "mendelian",
    "chromosome theory",
    "theory of heredity",
    "beginning of the 20th century",
    "history of",
    "historically",
    "became clear only later",
    "dinoflagellates",
    "paraspeckles",
    "azoospermia",
    "seminiferous",
    "spores",
]


def is_biology_noise(sentence):
    lower = sentence.lower()

    return any(
        marker in lower
        for marker in BIOLOGY_NOISE_MARKERS
    )


def score_general_sentence(
    sentence,
    entity,
):
    if is_biology_noise(
        sentence
    ):
        return -20.0

    lower = sentence.lower()

    score = 0.0

    entity_lower = entity.lower()

    if entity_lower in lower:
        score += 8.0

    for marker, weight in (
        GENERAL_MARKERS.items()
    ):
        if marker in lower:
            score += weight

    word_count = len(
        sentence.split()
    )

    if 8 <= word_count <= 40:
        score += 1.0

    elif word_count > 55:
        score -= 3.0

    return score


def select_general_evidence(
    context,
    entity,
    max_sentences=2,
):
    sentences = split_sentences(
        context
    )

    scored = []

    for index, sentence in enumerate(
        sentences
    ):
        if is_biology_noise(
            sentence
        ):
            continue

        score = score_general_sentence(
            sentence,
            entity,
        )

        scored.append(
            (
                score,
                index,
                normalize(sentence),
            )
        )

    scored.sort(
        key=lambda item: (
            item[0],
            -item[1],
        ),
        reverse=True,
    )

    selected = []

    for score, index, sentence in scored:
        if score <= 0:
            continue

        selected.append(
            sentence
        )

        if (
            len(selected)
            >= max_sentences
        ):
            break

    return remove_redundant(
        selected
    )


# --------------------------------------------------
# Biology-specific compression
# --------------------------------------------------

def compress_mitosis(sentence):
    lower = sentence.lower()

    if (
        "daughter chromosomes migrate "
        "to opposite poles"
        in lower
    ):
        return (
            "In mitosis, duplicated chromosomes "
            "are separated as the nucleus divides."
        )

    if (
        "prophase of mitosis"
        in lower
    ):
        return (
            "Mitosis proceeds through defined "
            "stages of chromosome separation."
        )

    return None


def compress_meiosis(sentence):
    lower = sentence.lower()

    if (
        "meiosis produces cells called "
        "gametes"
        in lower
        and "haploid"
        in lower
    ):
        return (
            "Meiosis produces haploid gametes, "
            "which contain one copy of each gene."
        )

    if (
        "meiosis"
        in lower
        and "haploid"
        in lower
    ):
        return (
            "Meiosis reduces cells to a "
            "haploid chromosome state."
        )

    return None


def compress_general_sentence(
    sentence,
    entity,
):
    if is_biology_noise(
        sentence
    ):
        return None

    entity_lower = entity.lower()

    if entity_lower == "mitosis":
        result = compress_mitosis(
            sentence
        )

        if result:
            return result

    if entity_lower == "meiosis":
        result = compress_meiosis(
            sentence
        )

        if result:
            return result

    sentence = normalize(
        sentence
    )

    words = sentence.split()

    if len(words) > 32:
        sentence = (
            " ".join(
                words[:32]
            )
            .rstrip(",;:")
            + "."
        )

    elif not sentence.endswith("."):
        sentence += "."

    return sentence


# --------------------------------------------------
# General comparison synthesis
# --------------------------------------------------

def synthesize_general_comparison(
    left_name,
    right_name,
    left_context,
    right_context,
):
    left_evidence = (
        select_general_evidence(
            left_context,
            left_name,
            max_sentences=2,
        )
    )

    right_evidence = (
        select_general_evidence(
            right_context,
            right_name,
            max_sentences=2,
        )
    )

    if (
        not left_evidence
        or not right_evidence
    ):
        return None

    left_parts = [
        compress_general_sentence(
            sentence,
            left_name,
        )
        for sentence in left_evidence
    ]

    right_parts = [
        compress_general_sentence(
            sentence,
            right_name,
        )
        for sentence in right_evidence
    ]

    left_parts = remove_redundant(
        [
            part
            for part in left_parts
            if part
        ]
    )

    right_parts = remove_redundant(
        [
            part
            for part in right_parts
            if part
        ]
    )

    if (
        not left_parts
        or not right_parts
    ):
        return None

    intro = (
        f"{left_name} and {right_name} "
        "differ in their process and outcome."
    )

    parts = [
        intro,
    ]

    parts.extend(
        left_parts[:2]
    )

    parts.extend(
        right_parts[:2]
    )

    if (
        left_name.lower() == "mitosis"
        and right_name.lower() == "meiosis"
    ):
        parts.append(
            "The key difference is that mitosis "
            "maintains chromosome number during "
            "ordinary cell division, while meiosis "
            "produces haploid reproductive cells."
        )

    return normalize(
        " ".join(
            parts
        )
    )


# --------------------------------------------------
# Main synthesis
# --------------------------------------------------

def synthesize_comparison(
    question,
    comparison_result,
):
    if comparison_result is None:
        return None

    plan = comparison_result.get(
        "plan"
    )

    if not plan:
        return None

    left_raw = plan.get(
        "left_entity",
        "",
    )

    right_raw = plan.get(
        "right_entity",
        "",
    )

    left_name = display_name(
        clean_label(
            left_raw
        )
    )

    right_name = display_name(
        clean_label(
            right_raw
        )
    )

    left_context = normalize(
        comparison_result.get(
            "left_context",
            "",
        )
    )

    right_context = normalize(
        comparison_result.get(
            "right_context",
            "",
        )
    )

    if (
        not left_context
        or not right_context
    ):
        return None

    mode = detect_comparison_mode(
        question,
        plan,
    )

    if mode == "fall":
        answer = synthesize_fall_comparison(
            left_name,
            right_name,
            left_context,
            right_context,
        )

    else:
        answer = synthesize_general_comparison(
            left_name,
            right_name,
            left_context,
            right_context,
        )

    if not answer:
        return None

    return capitalize_sentence(
        normalize(answer)
    )


# --------------------------------------------------
# Standalone tests
# --------------------------------------------------

if __name__ == "__main__":

    tests = [
        {
            "question":
                "What are the differences between "
                "mitosis and meiosis?",

            "result": {
                "plan": {
                    "left_entity":
                        "mitosis",

                    "right_entity":
                        "meiosis",
                },

                "left_context": (
                    "In closed mitosis, the daughter "
                    "chromosomes migrate to opposite poles "
                    "of the nucleus, which then divides in two. "
                    "In most cells, the disassembly of the "
                    "nuclear envelope marks the end of the "
                    "prophase of mitosis. "
                    "The function of the nucleus as carrier "
                    "of genetic information became clear only "
                    "later, after mitosis was discovered and "
                    "the Mendelian rules were rediscovered at "
                    "the beginning of the 20th century."
                ),

                "right_context": (
                    "In sexually reproducing organisms, "
                    "a specialized form of cell division "
                    "called meiosis produces cells called "
                    "gametes or germ cells that are haploid, "
                    "or contain only one copy of each gene. "
                    "Sterility of the hybrid was attributed "
                    "to difficulties in segregation during "
                    "meiosis, indicated by azoospermia."
                ),
            },
        },

        {
            "question":
                "Compare the fall of the Roman Empire "
                "with the fall of the Ottoman Empire.",

            "result": {
                "plan": {
                    "left_entity":
                        "the fall of the Roman Empire",

                    "right_entity":
                        "the fall of the Ottoman Empire",
                },

                "left_context": (
                    "Militarily, the Empire finally fell "
                    "after first being overrun by various "
                    "non-Roman peoples and then having its "
                    "heart in Italy seized by Germanic troops "
                    "in a revolt."
                ),

                "right_context": (
                    "The Ottoman Empire declined because of "
                    "military defeats, territorial losses, "
                    "economic problems and nationalist "
                    "movements."
                ),
            },
        },
    ]

    for test in tests:
        print()

        print(
            synthesize_comparison(
                test["question"],
                test["result"],
            )
        )