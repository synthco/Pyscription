# Pyscription

`pyscription` is a pest-powered Rust toolkit for extracting deterministic facts from Python
projects. It can walk individual files or entire source trees, normalize docstrings,
summarize imports, and assemble README-ready Markdown while keeping LLM prompts tiny.

## Features
- Recursively parse Python sources and emit structured [`ParsedItem`](crate::parser::ParsedItem)
  records for functions, classes, docstrings, and imports.
- Build module-level snapshots with [`aggregate_modules`](crate::report::aggregate_modules) and
  turn them into overview/API/docstring sections via [`generate_sections`](crate::generator::generate_sections).
- Drive the included CLI to produce terminal tables, JSON, or Markdown drafts enriched with an optional Gemini summary.
- Extend or replace the LLM bridge by implementing the [`GeminiClient`](crate::gemini::GeminiClient)
  trait, or reuse the testable [`MockGeminiClient`](crate::gemini::MockGeminiClient).

## CLI Quick Start
Run commands from the workspace root:

```bash
cargo run --manifest-path pyscription/Cargo.toml -- parse path/to/src
cargo run --manifest-path pyscription/Cargo.toml -- parse pkg --format json --module-root src
cargo run --manifest-path pyscription/Cargo.toml -- parse pkg --markdown README.generated.md
```

## Library Overview

| Module | Responsibility |
| --- | --- |
| `parser` | Pest grammar + helpers that produce `ParsedItem` values and validate docstrings. |
| `report` | Aggregates parsed artifacts into per-module snapshots (`ModuleReport`, `SymbolEntry`). |
| `generator` | Renders human-readable Markdown sections from aggregated data. |
| `gemini` | Defines a minimal client interface plus a blocking implementation and test mocks. |
| `error` | Shared `ParserError` type used by parsing helpers. |

## End-to-End Example
```rust no_run
use pyscription::generator::generate_sections;
use pyscription::parser::parse_module;
use pyscription::report::aggregate_modules;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let code = std::fs::read_to_string("examples/download.py")?;
    let items = parse_module(&code, "examples.download")?;

    // Aggregate per module, then reuse the same snapshot for reporting or LLM payloads.
    let modules = aggregate_modules(&items);
    let sections = generate_sections(&items);

    println!("{}", sections.overview);
    println!("{} module(s) indexed", modules.len());
    Ok(())
}
```

## Gemini
When `--markdown` is requested, the CLI builds a [`GeminiRequest`](crate::gemini::GeminiRequest)
containing normalized JSON plus short instructions. The default [`RealGeminiClient`](crate::gemini::RealGeminiClient)
reads API credentials from `GEMINI_API_KEY` or `pyscription/src/sercrets.yaml` and performs a blocking HTTP call
Tests can remain offline by seeding `MockGeminiClient` with deterministic responses.

## Errors
Parsing helpers return [`ParserError`](crate::error::ParserError), which distinguishes empty files,
unterminated docstrings, syntax issues surfaced by pest, and basic I/O failures. This makes it easy
to surface actionable diagnostics in custom frontends.
