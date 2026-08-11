import re
from collections import Counter


STOPWORDS = {
    "the", "a", "an", "and", "or", "but",
    "of", "to", "in", "on", "for", "with",
    "at", "by", "from", "as", "is", "was",
    "are", "were", "be", "been", "being",
    "that", "this", "these", "those",
    "it", "its", "they", "their", "them",
    "he", "she", "his", "her",
    "what", "when", "where", "why", "how",
    "did", "does", "do", "has", "have",
    "had",
}


def tokenize(text):
    return re.findall(
        r"[a-z0-9']+",
        text.lower(),
    )


def split_sentences(text):
    return [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )
        if sentence.strip()
    ]


def useful_words(text):
    return [
        word
        for word in tokenize(text)
        if word not in STOPWORDS
        and len(word) >= 3
    ]


def score_sentence(question, sentence):
    query_words = useful_words(question)

    sentence_words = useful_words(sentence)

    if not sentence_words:
        return 0.0

    query_counts = Counter(query_words)

    sentence_counts = Counter(
        sentence_words
    )

    score = 0.0

    for word, count in query_counts.items():
        if word in sentence_counts:
            score += (
                2.0
                * min(
                    count,
                    sentence_counts[word],
                )
            )

    # Extra weight for causal language
    # when question asks "why".
    if question.lower().startswith("why"):
        causal_markers = [
            "because",
            "due to",
            "caused by",
            "as a result",
            "therefore",
            "overrun",
            "revolt",
            "decline",
        ]

        lower_sentence = sentence.lower()

        for marker in causal_markers:
            if marker in lower_sentence:
                score += 1.5

    return score


def select_evidence(
    question,
    context,
    top_k=3,
):
    sentences = split_sentences(
        context
    )

    scored = []

    for index, sentence in enumerate(
        sentences
    ):
        score = score_sentence(
            question,
            sentence,
        )

        scored.append(
            (
                score,
                index,
                sentence,
            )
        )

    scored.sort(
        key=lambda item: (
            item[0],
            -item[1],
        ),
        reverse=True,
    )

    selected = [
        item
        for item in scored
        if item[0] > 0
    ][:top_k]

    if not selected:
        return sentences[:top_k]

    # Restore original document order.
    selected.sort(
        key=lambda item: item[1]
    )

    return [
        sentence
        for _, _, sentence
        in selected
    ]


if __name__ == "__main__":
    question = (
        "Why did the Roman Empire fall?"
    )

    context = (
        "Many theories have been advanced in way of explanation "
        "for decline of the Roman Empire, and many dates given "
        "for its fall. "
        "Militarily, however, the Empire finally fell after first "
        "being overrun by various non-Roman peoples and then having "
        "its heart in Italy seized by Germanic troops in a revolt. "
        "The historicity and exact dates are uncertain, and some "
        "historians do not consider that the Empire fell at this point."
    )

    evidence = select_evidence(
        question,
        context,
        top_k=3,
    )

    print("Question:")
    print(question)

    print("\nSelected evidence:")

    for i, sentence in enumerate(
        evidence,
        start=1,
    ):
        print(
            f"[{i}] {sentence}"
        )