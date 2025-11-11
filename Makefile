CARGO_DIR ?= pyscription
FILE ?= tests/examples/download.py
FORMAT ?= table
MODULE_ROOT ?=

.PHONY: fmt clippy test run ci build release

fmt:
	@cargo fmt --manifest-path $(CARGO_DIR)/Cargo.toml

clippy:
	@cargo clippy --manifest-path $(CARGO_DIR)/Cargo.toml --all-targets --all-features

test:
	@cargo test --manifest-path $(CARGO_DIR)/Cargo.toml

run:
	@MODULE_ARGS=""; \
	if [ -n "$(MODULE_ROOT)" ]; then MODULE_ARGS="--module-root $(MODULE_ROOT)"; fi; \
	cargo run --manifest-path $(CARGO_DIR)/Cargo.toml -- parse $(FILE) --format $(FORMAT) $$MODULE_ARGS

ci: fmt clippy test

build:
	@cargo build --manifest-path $(CARGO_DIR)/Cargo.toml

release:
	@cargo publish --manifest-path $(CARGO_DIR)/Cargo.toml --dry-run
