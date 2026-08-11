import re


# --------------------------------------------------
# Text helpers
# --------------------------------------------------

def normalize(text):
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def clean_entity(text):
    text = normalize(
        text
    )

    text = re.sub(
        r"^[\s:,-]+",
        "",
        text,
    )

    text = re.sub(
        r"[?.!]+$",
        "",
        text,
    )

    return text.strip()


# --------------------------------------------------
# Comparison detection
# --------------------------------------------------

def detect_comparison(question):
    """
    Detect explicit comparison questions.

    Returns:
        {
            "is_comparison": True,
            "left": "...",
            "right": "...",
        }

    or:

        {
            "is_comparison": False,
            "left": None,
            "right": None,
        }
    """

    q = normalize(
        question
    )

    patterns = [

        # ==========================================
        # Compare X with / to / and Y
        # ==========================================

        r"^compare (.+?) with "
        r"(.+?)[?.!]*$",

        r"^compare (.+?) to "
        r"(.+?)[?.!]*$",

        r"^compare (.+?) and "
        r"(.+?)[?.!]*$",

        # ==========================================
        # Explain / describe comparison
        # ==========================================

        r"^explain the differences between "
        r"(.+?) and (.+?)[?.!]*$",

        r"^explain the difference between "
        r"(.+?) and (.+?)[?.!]*$",

        r"^describe the differences between "
        r"(.+?) and (.+?)[?.!]*$",

        r"^describe the difference between "
        r"(.+?) and (.+?)[?.!]*$",

        r"^describe how (.+?) differs from "
        r"(.+?)[?.!]*$",

        r"^explain how (.+?) differs from "
        r"(.+?)[?.!]*$",

        r"^describe how (.+?) is different from "
        r"(.+?)[?.!]*$",

        r"^explain how (.+?) is different from "
        r"(.+?)[?.!]*$",

        # ==========================================
        # How does X compare...
        # ==========================================

        r"^how does (.+?) compare with "
        r"(.+?)[?.!]*$",

        r"^how does (.+?) compare to "
        r"(.+?)[?.!]*$",

        r"^how do (.+?) and (.+?) compare"
        r"[?.!]*$",

        # ==========================================
        # Difference between
        # ==========================================

        r"^what are the differences between "
        r"(.+?) and (.+?)[?.!]*$",

        r"^what are the main differences between "
        r"(.+?) and (.+?)[?.!]*$",

        r"^what are the key differences between "
        r"(.+?) and (.+?)[?.!]*$",

        r"^what is the difference between "
        r"(.+?) and (.+?)[?.!]*$",

        r"^what is the main difference between "
        r"(.+?) and (.+?)[?.!]*$",

        r"^differences between "
        r"(.+?) and (.+?)[?.!]*$",

        r"^main differences between "
        r"(.+?) and (.+?)[?.!]*$",

        r"^difference between "
        r"(.+?) and (.+?)[?.!]*$",

        # ==========================================
        # Different / differ
        # ==========================================

        r"^how are (.+?) and "
        r"(.+?) different[?.!]*$",

        r"^in what ways are (.+?) and "
        r"(.+?) different[?.!]*$",

        r"^in what ways do (.+?) and "
        r"(.+?) differ[?.!]*$",

        r"^how do (.+?) and "
        r"(.+?) differ[?.!]*$",

        r"^how is (.+?) different from "
        r"(.+?)[?.!]*$",

        r"^how are (.+?) different from "
        r"(.+?)[?.!]*$",

        r"^how does (.+?) differ from "
        r"(.+?)[?.!]*$",

        r"^how do (.+?) differ from "
        r"(.+?)[?.!]*$",

        r"^what differs between "
        r"(.+?) and (.+?)[?.!]*$",

        # ==========================================
        # Distinguishes / separates
        # ==========================================

        r"^what separates (.+?) from "
        r"(.+?)[?.!]*$",

        r"^what distinguishes (.+?) from "
        r"(.+?)[?.!]*$",

        r"^what differentiates (.+?) from "
        r"(.+?)[?.!]*$",

        # ==========================================
        # Versus / vs
        # ==========================================

        r"^(.+?) versus "
        r"(.+?)[?.!]*$",

        r"^(.+?) vs\.? "
        r"(.+?)[?.!]*$",
    ]

    for pattern in patterns:
        match = re.fullmatch(
            pattern,
            q,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        left = clean_entity(
            match.group(1)
        )

        right = clean_entity(
            match.group(2)
        )

        if not left or not right:
            continue

        # ------------------------------------------
        # Avoid identical comparisons
        # ------------------------------------------

        if (
            left.lower()
            == right.lower()
        ):
            continue

        return {
            "is_comparison":
                True,

            "left":
                left,

            "right":
                right,
        }

    return {
        "is_comparison":
            False,

        "left":
            None,

        "right":
            None,
    }


# --------------------------------------------------
# Query construction
# --------------------------------------------------

def build_comparison_queries(
    question,
):
    comparison = detect_comparison(
        question
    )

    if not comparison[
        "is_comparison"
    ]:
        return None

    left = comparison[
        "left"
    ]

    right = comparison[
        "right"
    ]

    return {
        "left_entity":
            left,

        "right_entity":
            right,

        "left_query":
            left,

        "right_query":
            right,
    }


# --------------------------------------------------
# Standalone tests
# --------------------------------------------------

if __name__ == "__main__":

    tests = [

        # ==========================================
        # Existing forms
        # ==========================================

        (
            "Compare the Roman Empire "
            "with the Ottoman Empire."
        ),

        (
            "Compare the fall of the Roman Empire "
            "with the fall of the Ottoman Empire."
        ),

        (
            "How does the Roman Empire compare "
            "with the Ottoman Empire?"
        ),

        (
            "What are the differences between "
            "mitosis and meiosis?"
        ),

        (
            "What is the difference between "
            "mitosis and meiosis?"
        ),

        (
            "How are mitosis and meiosis different?"
        ),

        (
            "Compare mitosis and meiosis."
        ),

        # ==========================================
        # Existing paraphrases
        # ==========================================

        (
            "Mitosis versus meiosis."
        ),

        (
            "Mitosis vs meiosis."
        ),

        (
            "What separates mitosis from meiosis?"
        ),

        (
            "How does mitosis differ from meiosis?"
        ),

        (
            "How is mitosis different from meiosis?"
        ),

        (
            "Differences between mitosis and meiosis."
        ),

        # ==========================================
        # V3 failed comparison forms
        # ==========================================

        (
            "Explain the differences between "
            "mitosis and meiosis."
        ),

        (
            "Describe how mitosis differs "
            "from meiosis."
        ),

        (
            "In what ways are mitosis "
            "and meiosis different?"
        ),

        (
            "What distinguishes mitosis "
            "from meiosis?"
        ),

        (
            "What are the main differences "
            "between mitosis and meiosis?"
        ),

        # ==========================================
        # Additional robustness forms
        # ==========================================

        (
            "Explain the difference between "
            "mitosis and meiosis."
        ),

        (
            "Describe the differences between "
            "mitosis and meiosis."
        ),

        (
            "Explain how mitosis differs "
            "from meiosis."
        ),

        (
            "What differentiates mitosis "
            "from meiosis?"
        ),

        (
            "How do mitosis and meiosis differ?"
        ),

        (
            "In what ways do mitosis "
            "and meiosis differ?"
        ),

        (
            "What are the key differences between "
            "mitosis and meiosis?"
        ),

        # ==========================================
        # Non-comparison guards
        # ==========================================

        (
            "Why did the Roman Empire fall?"
        ),

        (
            "Explain how photosynthesis works."
        ),

        (
            "What caused the Roman Empire "
            "to decline?"
        ),

        (
            "How was the Roman army organized?"
        ),

        (
            "Why was the Magna Carta important?"
        ),
    ]

    for question in tests:

        result = build_comparison_queries(
            question
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "Question:",
            question,
        )

        print(
            "Result:",
            result,
        )