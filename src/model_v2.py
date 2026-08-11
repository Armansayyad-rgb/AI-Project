import torch
import torch.nn as nn
import torch.nn.functional as F


MODEL_V2_CONFIG = {
    "vocab_size": 16000,
    "context_length": 512,
    "d_model": 576,
    "n_heads": 8,
    "n_layers": 12,
    "dropout": 0.1,
}


class CausalSelfAttention(nn.Module):
    def __init__(self, d_model, n_heads, dropout):
        super().__init__()

        assert d_model % n_heads == 0

        self.n_heads = n_heads
        self.head_dim = d_model // n_heads

        self.qkv = nn.Linear(
            d_model,
            3 * d_model,
        )

        self.out = nn.Linear(
            d_model,
            d_model,
        )

        self.dropout = dropout

    def forward(self, x):
        batch_size, seq_len, d_model = x.shape

        qkv = self.qkv(x)
        q, k, v = qkv.chunk(
            3,
            dim=-1,
        )

        q = q.view(
            batch_size,
            seq_len,
            self.n_heads,
            self.head_dim,
        ).transpose(1, 2)

        k = k.view(
            batch_size,
            seq_len,
            self.n_heads,
            self.head_dim,
        ).transpose(1, 2)

        v = v.view(
            batch_size,
            seq_len,
            self.n_heads,
            self.head_dim,
        ).transpose(1, 2)

        out = F.scaled_dot_product_attention(
            q,
            k,
            v,
            dropout_p=(
                self.dropout
                if self.training
                else 0.0
            ),
            is_causal=True,
        )

        out = out.transpose(
            1,
            2,
        ).contiguous()

        out = out.view(
            batch_size,
            seq_len,
            d_model,
        )

        return self.out(out)


class FeedForward(nn.Module):
    def __init__(self, d_model, dropout):
        super().__init__()

        hidden = 4 * d_model

        self.net = nn.Sequential(
            nn.Linear(
                d_model,
                hidden,
            ),
            nn.GELU(),
            nn.Linear(
                hidden,
                d_model,
            ),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)


class TransformerBlock(nn.Module):
    def __init__(self, config):
        super().__init__()

        self.ln1 = nn.LayerNorm(
            config["d_model"]
        )

        self.attn = CausalSelfAttention(
            config["d_model"],
            config["n_heads"],
            config["dropout"],
        )

        self.ln2 = nn.LayerNorm(
            config["d_model"]
        )

        self.ffn = FeedForward(
            config["d_model"],
            config["dropout"],
        )

    def forward(self, x):
        x = x + self.attn(
            self.ln1(x)
        )

        x = x + self.ffn(
            self.ln2(x)
        )

        return x


class SmallLMV2(nn.Module):
    def __init__(self, config=MODEL_V2_CONFIG):
        super().__init__()

        self.vocab_size = config[
            "vocab_size"
        ]

        self.context_length = config[
            "context_length"
        ]

        self.d_model = config[
            "d_model"
        ]

        self.token_embedding = nn.Embedding(
            self.vocab_size,
            self.d_model,
        )

        self.position_embedding = nn.Embedding(
            self.context_length,
            self.d_model,
        )

        self.dropout = nn.Dropout(
            config["dropout"]
        )

        self.blocks = nn.ModuleList(
            [
                TransformerBlock(config)
                for _ in range(
                    config["n_layers"]
                )
            ]
        )

        self.final_norm = nn.LayerNorm(
            self.d_model
        )

        self.lm_head = nn.Linear(
            self.d_model,
            self.vocab_size,
            bias=False,
        )

        self.lm_head.weight = (
            self.token_embedding.weight
        )

        self.apply(
            self._init_weights
        )

    def _init_weights(self, module):
        if isinstance(
            module,
            nn.Linear,
        ):
            nn.init.normal_(
                module.weight,
                mean=0.0,
                std=0.02,
            )

            if module.bias is not None:
                nn.init.zeros_(
                    module.bias
                )

        elif isinstance(
            module,
            nn.Embedding,
        ):
            nn.init.normal_(
                module.weight,
                mean=0.0,
                std=0.02,
            )

    def forward(
        self,
        input_ids,
        targets=None,
    ):
        batch_size, seq_len = (
            input_ids.shape
        )

        if seq_len > self.context_length:
            raise ValueError(
                f"Sequence length {seq_len} "
                f"exceeds context length "
                f"{self.context_length}"
            )

        positions = torch.arange(
            seq_len,
            device=input_ids.device,
        )

        x = (
            self.token_embedding(
                input_ids
            )
            + self.position_embedding(
                positions
            )
        )

        x = self.dropout(x)

        for block in self.blocks:
            x = block(x)

        x = self.final_norm(x)

        logits = self.lm_head(x)

        loss = None

        if targets is not None:
            loss = F.cross_entropy(
                logits.view(
                    -1,
                    self.vocab_size,
                ),
                targets.view(-1),
                ignore_index=-100,
            )

        return logits, loss


if __name__ == "__main__":
    model = SmallLMV2()

    total_params = sum(
        p.numel()
        for p in model.parameters()
    )

    print(
        f"Total parameters: "
        f"{total_params:,}"
    )

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    model = model.to(device)

    print("Device:", device)

    test_input = torch.randint(
        0,
        MODEL_V2_CONFIG[
            "vocab_size"
        ],
        (1, 128),
        device=device,
    )

    with torch.no_grad():
        logits, _ = model(
            test_input
        )

    print(
        "Input shape:",
        test_input.shape,
    )

    print(
        "Output shape:",
        logits.shape,
    )

    if device == "cuda":
        print(
            "Allocated VRAM MB:",
            round(
                torch.cuda.memory_allocated()
                / 1024**2,
                1,
            ),
        )

    print(
        "Model V2 test successful!"
    )