import math
import torch
import torch.nn as nn
import torch.nn.functional as F

from config import MODEL_CONFIG


class CausalSelfAttention(nn.Module):
    def __init__(self, d_model, n_heads, dropout):
        super().__init__()

        assert d_model % n_heads == 0

        self.n_heads = n_heads
        self.head_dim = d_model // n_heads

        self.qkv = nn.Linear(d_model, 3 * d_model)
        self.out = nn.Linear(d_model, d_model)

        self.attn_dropout = dropout
        self.resid_dropout = nn.Dropout(dropout)

    def forward(self, x):
        batch_size, seq_len, d_model = x.shape

        qkv = self.qkv(x)
        q, k, v = qkv.chunk(3, dim=-1)

        q = q.view(
            batch_size, seq_len, self.n_heads, self.head_dim
        ).transpose(1, 2)

        k = k.view(
            batch_size, seq_len, self.n_heads, self.head_dim
        ).transpose(1, 2)

        v = v.view(
            batch_size, seq_len, self.n_heads, self.head_dim
        ).transpose(1, 2)

        attention = F.scaled_dot_product_attention(
            q,
            k,
            v,
            dropout_p=self.attn_dropout if self.training else 0.0,
            is_causal=True,
        )

        attention = attention.transpose(1, 2).contiguous()
        attention = attention.view(batch_size, seq_len, d_model)

        return self.resid_dropout(self.out(attention))


class FeedForward(nn.Module):
    def __init__(self, d_model, dropout):
        super().__init__()

        hidden_size = 4 * d_model

        self.net = nn.Sequential(
            nn.Linear(d_model, hidden_size),
            nn.GELU(),
            nn.Linear(hidden_size, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)


class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, dropout):
        super().__init__()

        self.ln1 = nn.LayerNorm(d_model)
        self.attention = CausalSelfAttention(
            d_model,
            n_heads,
            dropout,
        )

        self.ln2 = nn.LayerNorm(d_model)
        self.ffn = FeedForward(
            d_model,
            dropout,
        )

    def forward(self, x):
        x = x + self.attention(self.ln1(x))
        x = x + self.ffn(self.ln2(x))

        return x


class SmallLM(nn.Module):
    def __init__(self, config=MODEL_CONFIG):
        super().__init__()

        self.vocab_size = config["vocab_size"]
        self.context_length = config["context_length"]
        self.d_model = config["d_model"]

        self.token_embedding = nn.Embedding(
            self.vocab_size,
            self.d_model,
        )

        self.position_embedding = nn.Embedding(
            self.context_length,
            self.d_model,
        )

        self.dropout = nn.Dropout(config["dropout"])

        self.blocks = nn.ModuleList(
            [
                TransformerBlock(
                    config["d_model"],
                    config["n_heads"],
                    config["dropout"],
                )
                for _ in range(config["n_layers"])
            ]
        )

        self.final_norm = nn.LayerNorm(self.d_model)

        self.lm_head = nn.Linear(
            self.d_model,
            self.vocab_size,
            bias=False,
        )

        # Share token embedding and output weights.
        self.lm_head.weight = self.token_embedding.weight

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(
                module.weight,
                mean=0.0,
                std=0.02,
            )

            if module.bias is not None:
                nn.init.zeros_(module.bias)

        elif isinstance(module, nn.Embedding):
            nn.init.normal_(
                module.weight,
                mean=0.0,
                std=0.02,
            )

    def forward(self, input_ids, targets=None):
        batch_size, seq_len = input_ids.shape

        if seq_len > self.context_length:
            raise ValueError(
                f"Sequence length {seq_len} exceeds "
                f"context length {self.context_length}"
            )

        positions = torch.arange(
            0,
            seq_len,
            device=input_ids.device,
        )

        token_embeddings = self.token_embedding(input_ids)
        position_embeddings = self.position_embedding(positions)

        x = token_embeddings + position_embeddings
        x = self.dropout(x)

        for block in self.blocks:
            x = block(x)

        x = self.final_norm(x)

        logits = self.lm_head(x)

        loss = None

        if targets is not None:
            loss = F.cross_entropy(
                logits.view(-1, self.vocab_size),
                targets.view(-1),
            )

        return logits, loss


if __name__ == "__main__":
    model = SmallLM()

    total_params = sum(
        p.numel() for p in model.parameters()
    )

    trainable_params = sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )

    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    print(f"Device: {device}")

    test_input = torch.randint(
        0,
        MODEL_CONFIG["vocab_size"],
        (2, 64),
        device=device,
    )

    logits, _ = model(test_input)

    print("Input shape:", test_input.shape)
    print("Output shape:", logits.shape)
    print("Model test successful!")