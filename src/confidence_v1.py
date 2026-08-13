import re


def extraction_confidence(
    question,
    context,
    answer,
):
    """
    Estimate how strongly an extracted answer is supported
    by the retrieved context.

    Returns a float from 0.0 to 1.0.
    """

    if not answer:
        return 0.0

    q = question.lower().strip()
    c = context.lower()
    a = answer.lower().strip()

    score = 0.0

    # --------------------------------------------------
    # 1. The extracted answer should actually be
    #    grounded in the retrieved context.
    # --------------------------------------------------

    normalized_answer = re.sub(
        r"\s+",
        " ",
        a,
    )

    normalized_context = re.sub(
        r"\s+",
        " ",
        c,
    )

    # Remove common formatting words added by extractor.
    evidence_answer = normalized_answer

    prefixes = [
        "because ",
        "it was due to ",
        "it happened as a result of ",
    ]

    for prefix in prefixes:
        if evidence_answer.startswith(prefix):
            evidence_answer = evidence_answer[
                len(prefix):
            ]

    evidence_answer = evidence_answer.rstrip(".")

    if (
        evidence_answer
        and evidence_answer
        in normalized_context
    ):
        score += 0.50

    # --------------------------------------------------
    # 2. Question-type evidence
    # --------------------------------------------------

    if "born" in q:
        if re.search(
            r"\bwas born (?:on|in)\b",
            c,
        ):
            score += 0.35

    elif "founded" in q:
        if re.search(
            r"\bwas founded in\b",
            c,
        ):
            score += 0.35

    elif "established" in q:
        if re.search(
            r"\bwas established in\b",
            c,
        ):
            score += 0.35

    elif "released" in q:
        if re.search(
            r"\bwas released in\b",
            c,
        ):
            score += 0.35

    elif "published" in q:
        if re.search(
            r"\bwas published in\b",
            c,
        ):
            score += 0.35

    elif "named after" in q:
        if re.search(
            r"\bwas named after\b",
            c,
        ):
            score += 0.35

    elif (
        q.startswith("why ")
        or q.startswith("what caused ")
    ):
        causal_patterns = [
            r"\bbecause\b",
            r"\bdue to\b",
            r"\bas a result of\b",
            r"\bwas caused by\b",
            r"\bfell after\b",
        ]

        if any(
            re.search(pattern, c)
            for pattern in causal_patterns
        ):
            score += 0.35

    # --------------------------------------------------
    # 3. Basic answer sanity
    # --------------------------------------------------

    if 1 <= len(answer.split()) <= 45:
        score += 0.10

    # --------------------------------------------------
    # 4. Penalize suspicious output
    # --------------------------------------------------

    if len(answer) > 300:
        score -= 0.30

    if re.search(
        r"(.)\1{5,}",
        answer,
    ):
        score -= 0.30

    return max(
        0.0,
        min(score, 1.0),
    )


if __name__ == "__main__":

    tests = [
        (
            "When was John McCain born?",
            (
                "John McCain was born on "
                "August 29 , 1936 , at Coco Solo "
                "Naval Air Station."
            ),
            "August 29 , 1936",
        ),
        (
            "Why was Kaua'i chosen over Mexico?",
            (
                "Kaua'i was chosen over Mexico "
                "because a tax credit for in-state "
                "spending was negotiated with the "
                "Kaua'i Film Commission."
            ),
            (
                "Because a tax credit for in-state "
                "spending was negotiated with the "
                "Kaua'i Film Commission."
            ),
        ),
        (
            "When was John McCain born?",
            (
                "John McCain served in the "
                "United States Senate."
            ),
            "August 29 , 1936",
        ),
    ]

    for question, context, answer in tests:
        confidence = extraction_confidence(
            question,
            context,
            answer,
        )

        print("Question:", question)
        print("Answer:", answer)
        print(
            "Confidence:",
            f"{confidence:.2f}",
        )
        print("-" * 60)
        