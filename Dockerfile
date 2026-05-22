# ═══════════════════════════════════════════════════════════════════════════════
# State Machine Kernel — Rust
# ═══════════════════════════════════════════════════════════════════════════════

# ── base: toolchain ───────────────────────────────────────────────────────────
FROM rust:latest AS base
WORKDIR /app
RUN rustup component add rustfmt clippy

# ── builder: compile ──────────────────────────────────────────────────────────
FROM base AS builder
COPY . .
RUN cargo build --release

# ── tester: fmt · clippy · tests ──────────────────────────────────────────────
FROM base AS tester
COPY . .
RUN cargo fmt -- --check
RUN cargo clippy -- -D warnings
RUN cargo test --verbose

# ── runtime: production ───────────────────────────────────────────────────────
FROM debian:bookworm-slim AS runtime
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/chitragupt /usr/local/bin/
EXPOSE 8080
CMD ["chitragupt"]
