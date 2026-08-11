from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import ByteLevel
from tokenizers.decoders import ByteLevel as ByteLevelDecoder
from tokenizers.processors import TemplateProcessing

DATA_FILE = r"C:\AI-Project\data\wikitext_v2.txt"
OUTPUT_FILE = r"C:\AI-Project\data\tokenizer_v2.json"

VOCAB_SIZE = 16000

tokenizer = Tokenizer(
    BPE(unk_token="<UNK>")
)

tokenizer.pre_tokenizer = ByteLevel(
    add_prefix_space=False
)

tokenizer.decoder = ByteLevelDecoder()

trainer = BpeTrainer(
    vocab_size=VOCAB_SIZE,
    min_frequency=2,
    special_tokens=[
        "<PAD>",
        "<BOS>",
        "<EOS>",
        "<UNK>",
        "<SEARCH>",
        "<RESULT>",
        "<TOOL>",
        "<ANSWER>",
    ],
    initial_alphabet=ByteLevel.alphabet(),
)

tokenizer.train(
    files=[DATA_FILE],
    trainer=trainer,
)

bos_id = tokenizer.token_to_id("<BOS>")
eos_id = tokenizer.token_to_id("<EOS>")

tokenizer.post_processor = TemplateProcessing(
    single="<BOS> $A <EOS>",
    special_tokens=[
        ("<BOS>", bos_id),
        ("<EOS>", eos_id),
    ],
)

tokenizer.save(OUTPUT_FILE)

print("Tokenizer saved to:", OUTPUT_FILE)
print("Vocabulary size:", tokenizer.get_vocab_size())

test_text = (
    "Artificial intelligence can retrieve "
    "knowledge and reason over evidence."
)

encoded = tokenizer.encode(test_text)

print("Tokens:", encoded.tokens)
print("Decoded:", tokenizer.decode(encoded.ids))