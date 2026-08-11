import argparse
import sys

import torch
from tokenizers import Tokenizer

from model import SmallLM

TOKENIZER_FILE = r"C:\AI-Project\data\tokenizer.json"
MODEL_FILE = r"C:\AI-Project\checkpoints\final_model.pt"

MAX_NEW_TOKENS = 100
TEMPERATURE = 0.8
TOP_K = 40


def generate(model, tokenizer, prompt, device):
    encoded = tokenizer.encode(prompt)
    token_ids = encoded.ids

    # Remove EOS so generation doesn't start after an end marker.
    eos_id = tokenizer.token_to_id("<EOS>")
    bos_id = tokenizer.token_to_id("<BOS>")

    if token_ids and token_ids[-1] == eos_id:
        token_ids = token_ids[:-1]

    x = torch.tensor(
        [token_ids],
        dtype=torch.long,
        device=device,
    )

    model.eval()

    with torch.no_grad():
        for _ in range(MAX_NEW_TOKENS):

            # Respect model context length
            x_input = x[:, -model.context_length:]

            logits, _ = model(x_input)

            # Last-token prediction
            logits = logits[:, -1, :] / TEMPERATURE

            # Top-k sampling
            k = min(TOP_K, logits.size(-1))
            values, _ = torch.topk(logits, k)

            cutoff = values[:, -1].unsqueeze(-1)

            logits = torch.where(
                logits < cutoff,
                torch.full_like(logits, float("-inf")),
                logits,
            )

            probs = torch.softmax(logits, dim=-1)

            next_token = torch.multinomial(
                probs,
                num_samples=1,
            )

            x = torch.cat(
                [x, next_token],
                dim=1,
            )

            if next_token.item() == eos_id:
                break

    output_ids = x[0].tolist()

    # Remove BOS/EOS from displayed output
    output_ids = [
        token_id
        for token_id in output_ids
        if token_id not in (bos_id, eos_id)
    ]

    return tokenizer.decode(output_ids)


def run_prompt(prompt, model, tokenizer, device):
    """Process a single prompt and print the model's response."""
    if not prompt:
        return

    response = generate(
        model,
        tokenizer,
        prompt,
        device,
    )

    print("\nModel:", response)


def main():
    parser = argparse.ArgumentParser(
        description="Generate text from the SmallLM model."
    )
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        help="Single prompt (non-interactive mode)",
    )
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("Device:", device)

    tokenizer = Tokenizer.from_file(TOKENIZER_FILE)

    model = SmallLM().to(device)

    state_dict = torch.load(
        MODEL_FILE,
        map_location=device,
        weights_only=True,
    )

    model.load_state_dict(state_dict)

    print("Model loaded.")

    # Non-interactive (batch) mode: process a single prompt and exit.
    if args.query is not None:
        run_prompt(args.query.strip(), model, tokenizer, device)
        return

    print("Type 'quit' to exit.")

    # Interactive mode.
    try:
        while True:
            prompt = input("\nYou: ").strip()

            if prompt.lower() == "quit":
                break

            if not prompt:
                continue

            run_prompt(prompt, model, tokenizer, device)
    except (EOFError, KeyboardInterrupt):
        print("\n\nNo input provided. Exiting gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
