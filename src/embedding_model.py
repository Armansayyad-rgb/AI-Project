import torch
import torch.nn as nn
import torch.nn.functional as F

from config import MODEL_CONFIG


class TextEmbeddingModel(nn.Module):
    def __init__(
        self,
        vocab_size,
        d_model=256,
        n_heads=4,
        n_layers=4,
        max_length=256,
        embedding_dim=256,
        dropout=0.1,
    ):
        super().__init__()

        self.max_length = max_length

        self.token_embedding = nn.Embedding(
            vocab_size,
            d_model,
        )

        self.position_embedding = nn.Embedding(
            max_length,
            d_model,
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=4 * d_model,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=n_layers,
        )

        self.final_norm = nn.LayerNorm(d_model)

        self.projection = nn.Linear(
            d_model,
            embedding_dim,
        )

    def forward(self, input_ids, attention_mask=None):
        batch_size, seq_len = input_ids.shape

        if seq_len > self.max_length:
            raise ValueError(
                f"Sequence length {seq_len} exceeds "
                f"maximum {self.max_length}"
            )

        positions = torch.arange(
            seq_len,
            device=input_ids.device,
        )

        x = (
            self.token_embedding(input_ids)
            + self.position_embedding(positions)
        )

        if attention_mask is not None:
            padding_mask = attention_mask == 0
        else:
            padding_mask = None

        x = self.encoder(
            x,
            src_key_padding_mask=padding_mask,
        )

        x = self.final_norm(x)

        if attention_mask is None:
            pooled = x.mean(dim=1)
        else:
            mask = attention_mask.unsqueeze(-1)
            x = x * mask

            pooled = x.sum(dim=1) / mask.sum(
                dim=1
            ).clamp(min=1)

        embedding = self.projection(pooled)

        embedding = F.normalize(
            embedding,
            p=2,
            dim=-1,
        )

        return embedding


if __name__ == "__main__":
    model = TextEmbeddingModel(
        vocab_size=MODEL_CONFIG["vocab_size"]
    )

    total_params = sum(
        p.numel()
        for p in model.parameters()
    )

    print(
        f"Embedding model parameters: "
        f"{total_params:,}"
    )

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    model = model.to(device)

    test_input = torch.randint(
        0,
        MODEL_CONFIG["vocab_size"],
        (2, 64),
        device=device,
    )

    embeddings = model(test_input)

    print("Device:", device)
    print("Output shape:", embeddings.shape)
    print(
        "First embedding norm:",
        embeddings[0].norm().item(),
    )
    print("Embedding model test successful!")