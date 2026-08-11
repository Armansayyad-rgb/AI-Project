import re


def normalize_spaces(text):
    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def extract_birth_date(question, context):
    if "born" not in question.lower():
        return None

    patterns = [
        r"was born on ([A-Za-z]+ \d{1,2} ,? \d{4})",
        r"was born in (\d{4})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            context,
            flags=re.IGNORECASE,
        )

        if match:
            return normalize_spaces(
                match.group(1)
            )

    return None


def extract_founded_year(question, context):
    q = question.lower()

    if not any(
        word in q
        for word in {
            "founded",
            "established",
        }
    ):
        return None

    patterns = [
        r"was founded in (\d{4})",
        r"was established in (\d{4})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            context,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None


def extract_release_year(question, context):
    if "released" not in question.lower():
        return None

    match = re.search(
        r"was released in (\d{4})",
        context,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


def extract_published_year(question, context):
    if "published" not in question.lower():
        return None

    match = re.search(
        r"was published in (\d{4})",
        context,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


def extract_named_after(question, context):
    if "named after" not in question.lower():
        return None

    match = re.search(
        r"was named after (.+?)(?:[.;]|$)",
        context,
        flags=re.IGNORECASE,
    )

    if match:
        return normalize_spaces(
            match.group(1)
        )

    return None


def extract_fall_cause(question, context):
    q = question.lower().strip()

    if not (
        q.startswith("why ")
        and any(
            word in q
            for word in {
                "fall",
                "fell",
                "collapse",
                "collapsed",
            }
        )
    ):
        return None

    patterns = [
        (
            r"\b(?:finally )?fell after "
            r"(.+?)(?:[.;]|$)",
            "{}",
        ),
        (
            r"\bcollapsed after "
            r"(.+?)(?:[.;]|$)",
            "{}",
        ),
        (
            r"\bfell when "
            r"(.+?)(?:[.;]|$)",
            "{}",
        ),
    ]

    for pattern, template in patterns:
        match = re.search(
            pattern,
            context,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        cause = normalize_spaces(
            match.group(1)
        )

        if len(cause) < 5:
            continue

        if len(cause) > 300:
            continue

        answer = template.format(cause)

        if not answer.endswith("."):
            answer += "."

        return answer

    return None


def extract_causal_answer(question, context):
    q = question.lower().strip()

    if not (
        q.startswith("why ")
        or q.startswith("what caused ")
    ):
        return None

    patterns = [
        (
            r"\bbecause (.+?)(?:[.;]|$)",
            "Because {}",
        ),
        (
            r"\bdue to (.+?)(?:[.;]|$)",
            "It was due to {}",
        ),
        (
            r"\bas a result of (.+?)(?:[.;]|$)",
            "It happened as a result of {}",
        ),
        (
            r"\bwas caused by (.+?)(?:[.;]|$)",
            "{}",
        ),
    ]

    for pattern, template in patterns:
        match = re.search(
            pattern,
            context,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        cause = normalize_spaces(
            match.group(1)
        )

        if len(cause) < 3:
            continue

        if len(cause) > 220:
            continue

        answer = template.format(cause)

        if not answer.endswith("."):
            answer += "."

        return answer

    return None


def extract_answer(question, context):
    extractors = [
        extract_birth_date,
        extract_founded_year,
        extract_release_year,
        extract_published_year,
        extract_named_after,

        # Try the specific fall/collapse extractor
        # before the more general causal extractor.
        extract_fall_cause,
        extract_causal_answer,
    ]

    for extractor in extractors:
        answer = extractor(
            question,
            context,
        )

        if answer:
            return answer

    return None


if __name__ == "__main__":
    tests = [
        (
            "When was John McCain born?",
            (
                "John McCain was born on August 29 , 1936 , "
                "at Coco Solo Naval Air Station."
            ),
        ),
        (
            "Why was Kaua'i chosen over Mexico?",
            (
                "Kaua'i was chosen over Mexico because "
                "a tax credit for in-state spending was negotiated "
                "with the Kaua'i Film Commission."
            ),
        ),
        (
            "What caused the most damaging Lock Haven flood?",
            (
                "The most damaging Lock Haven flood was caused by "
                "the remnants of Hurricane Agnes in 1972."
            ),
        ),
        (
            "Why did the Roman Empire fall?",
            (
                "Many theories have been advanced for the decline "
                "of the Roman Empire. Militarily, however, the Empire "
                "finally fell after first being overrun by various "
                "non-Roman peoples and then having its heart in Italy "
                "seized by Germanic troops in a revolt."
            ),
        ),
    ]

    for question, context in tests:
        answer = extract_answer(
            question,
            context,
        )

        print(
            "Question:",
            question,
        )

        print(
            "Extracted answer:",
            answer,
        )

        print("-" * 60)