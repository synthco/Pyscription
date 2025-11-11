# Pyscription: Token-Efficient README Generator

Pyscription is a Rust CLI that walks Python projects, extracts deterministic API facts, and spends LLM tokens only on the prose that still needs a human touch. The tool records every function, class, import, and docstring that the grammar encounters, then assembles a README draft that is dramatically cheaper than sending an entire repository to a model.

---
## Key Capabilities
- Recursively scan any `.py` file or directory, autodetect the module root using workspace markers (`pyproject.toml`, `setup.cfg`, `.git`), or honor an explicit `--module-root DIR`.
- Parse four grammar rules—`function_def`, `class_def`, `docstring`, `import_stmt`—so both callable declarations and metadata (docstrings/imports) feed downstream reports.
- Emit parse results as a terminal table (default) or machine-readable JSON (`--format json`) for tooling integrations.
- Generate README-ready Markdown by passing `--markdown out.md`; deterministic sections (overview, API tables, docstring coverage) are stitched with an ≤80-word Gemini summary when available.
- Serialize the parsed structure into a compact JSON payload shared with Gemini so the LLM sees the same modules, symbols, and docstring coverage that appear in the README; only the first 8 modules and 8 symbols per kind are ever sent.
- Preserve provenance for every parsed item (line, column, module, optional source path) so downstream tooling can link back to code, and expose a `credits` subcommand for attribution.

## How It Works
1. **Deterministic parsing.** `parser.rs` (backed by `parser.pest`) defines the grammar rules above. Each match becomes a `ParsedItem` containing the rule, normalized content, location, and module metadata. Docstrings are validated up-front so unterminated literals surface as parser errors.
2. **Aggregation + section generation.** `report.rs` groups items per module and normalizes symbol lists. `generator.rs` reuses that snapshot to render Overview, API tables, and docstring coverage without duplicate logic between the CLI table, JSON output, and Markdown generator.
3. **Optional narrative layer.** When `--markdown` is provided, `main.rs` builds a payload capped at 15 modules / 15 functions / 15 classes per module and asks `gemini.rs` for a summary. If the client cannot connect, the README still renders with a fallback notice.

Because the parser operates on a bounded grammar, the resulting dataset can be shared, diffed, or cached before sending the tiny subset of information to an LLM.

### Grammar 
```pest
function_def = @{
    decorator_line* ~ indentation? ~ async_prefix? ~ "def" ~ WHITESPACE+ ~ identifier ~ function_signature_tail
}
class_def = @{
    decorator_line* ~ indentation? ~ "class" ~ WHITESPACE+ ~ identifier ~ class_signature_tail
}
docstring = @{ indentation? ~ triple_quote ~ docstring_body? ~ triple_quote }
import_stmt = @{ indentation? ~ (plain_import | from_import) ~ NEWLINE? }
```
## Quick Start
Run everything from the repository root:

```bash
make run FILE=tests/examples/download.py
make run FILE=src FORMAT=json
make run FILE=src FORMAT=table MODULE_ROOT=src
```

Use the raw `cargo` invocations when you need extra flags (such as `--markdown`):

```bash
cargo run --manifest-path pyscription/Cargo.toml -- parse src
cargo run --manifest-path pyscription/Cargo.toml -- parse pkg --format json --module-root src
cargo run --manifest-path pyscription/Cargo.toml -- parse pkg --markdown README.generated.md
cargo run --manifest-path pyscription/Cargo.toml -- credits
```

## CLI Commands & Flags
- `parse PATH` (default subcommand) – analyze a file or directory; directories are traversed recursively for `.py`.
  - `--format {table,json}` – choose between human-readable output and JSON (table is default).
  - `--module-root DIR` – force a module base path when auto-detection is wrong (monorepos, nested packages).
  - `--markdown FILE` – write README-ready Markdown to `FILE` while still printing the requested format to stdout.
- `credits` – print attribution for the CLI.

## Gemini
- Provide an API key through `GEMINI_API_KEY` or `pyscription/src/sercrets.yaml` (typo preserved to match the source).
- The CLI works offline. If Gemini connectivity fails, a warning is emitted and the README summary is replaced with a placeholder.
- Module/LLM payload limits (`MAX_LLM_MODULES = 15`, `MAX_LLM_SYMBOLS_PER_KIND = 15`) are enforced so requests stay within context limits, and any truncation notice is echoed to stderr before writing Markdown.
- To exercise the live Gemini call, export `GEMINI_API_KEY` and set `PYSCRIPTION_RUN_GEMINI_LIVE_TEST=1`, then run `cargo test --manifest-path pyscription/Cargo.toml --test gemini_online -- --ignored`. The test treats transient Gemini outages (e.g., `503`) as a skip so pipelines stay tolerant.

## Project Layout
- `pyscription/src/cli.rs` – clap-based CLI definition (parse + credits commands and `--format/--markdown` flags).
- `pyscription/src/main.rs` – orchestrates file discovery, module-root detection, reporting, optional Markdown generation, and output formatting
- `pyscription/src/parser.rs` + `parser.pest` – pest grammar and helpers that produce `ParsedItem` records for functions, classes, docstrings, and imports.
- `pyscription/src/report.rs` – aggregates parsed items per module and normalizes symbol metadata for generators and Gemini payloads.
- `pyscription/src/generator.rs` – renders deterministic Markdown sections (overview, per-module API tables, docstring coverage).
- `pyscription/src/gemini.rs` – thin Gemini client plus test-safe mocks; builds `GeminiRequest` objects shared across the CLI.
- `pyscription/src/error.rs` – parser error definitions (empty file, unterminated docstring, syntax/IO issues).
- `pyscription/tests/parser_tests.rs` – shared regression tests with fixtures in `tests/examples/`.

