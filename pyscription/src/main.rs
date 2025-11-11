mod cli;
use anyhow::{Context, Result, bail};
use clap::Parser;
use cli::{Cli, Commands, OutputFormat};
use pyscription::gemini::{GeminiClient, GeminiRequest, RealGeminiClient};
use pyscription::generator::generate_sections;
use pyscription::parser::{ParsedItem, parse_module};
use pyscription::report::{ModuleReport, SymbolEntry, aggregate_modules};
use serde_json::{Value, json};
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process;

const MAX_LLM_MODULES: usize = 15;
const MAX_LLM_SYMBOLS_PER_KIND: usize = 15;

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Parse {
            path,
            format,
            module_root,
            markdown,
        } => {
            if let Err(e) = run_parse(&path, format, module_root.as_deref(), markdown.as_deref()) {
                eprintln!("Error: {e}");
                process::exit(1);
            }
        }
        Commands::Credits => {
            println!("Pyscription (pest-powered) — Made by Ivan Tyshchenko");
        }
    }
    Ok(())
}

fn run_parse(
    path: &str,
    format: OutputFormat,
    module_root: Option<&str>,
    markdown: Option<&str>,
) -> Result<()> {
    let input_path = PathBuf::from(path);
    if !input_path.exists() {
        bail!("Path '{}' does not exist", path);
    }

    let module_root_path = module_root
        .map(PathBuf::from)
        .or_else(|| autodetect_module_root(&input_path))
        .unwrap_or_else(|| {
            if input_path.is_file() {
                input_path
                    .parent()
                    .map(PathBuf::from)
                    .unwrap_or_else(|| PathBuf::from("."))
            } 
            else {
                input_path.clone()
            }
        });
    let module_root_canon = module_root_path
        .canonicalize()
        .unwrap_or(module_root_path.clone());

    let files = collect_python_files(&input_path)?;
    let all_items = if let Some(md_path) = markdown {
        let md_path = PathBuf::from(md_path);
        let items = to_markdown(&files, &module_root_canon, &md_path)?;
        println!("Markdown written to {}", md_path.display());
        items
    } 
    else {
        parse_python_files(&files, &module_root_canon)?
    };

    match format {
        OutputFormat::Table => print_table(&all_items),
        OutputFormat::Json => print_json(&all_items)?,
    };

    Ok(())
}

fn collect_python_files(path: &Path) -> Result<Vec<PathBuf>> {
    if path.is_file() {
        return Ok(vec![path.to_path_buf()]);
    }

    if !path.is_dir() {
        bail!("Path '{}' is neither a file nor directory", path.display());
    }

    let mut files = Vec::new();
    walk_python_files(path, &mut files)?;
    files.sort();
    if files.is_empty() {
        bail!("No Python files found under '{}'", path.display());
    }
    Ok(files)
}

fn parse_python_files(files: &[PathBuf], module_root: &Path) -> Result<Vec<ParsedItem>> {
    let mut all_items = Vec::new();
    for file in files {
        let content = fs::read_to_string(file)
            .with_context(|| format!("Failed to read {}", file.display()))?;
        let module_name = module_name_from_path(file, module_root);
        let mut parsed = parse_module(&content, &module_name)?;
        let source_path = file.display().to_string();
        for item in &mut parsed {
            item.source = Some(source_path.clone());
        }
        all_items.extend(parsed);
    }
    Ok(all_items)
}

fn walk_python_files(dir: &Path, files: &mut Vec<PathBuf>) -> Result<()> {
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            walk_python_files(&path, files)?;
        } else if path.extension().map(|ext| ext == "py").unwrap_or(false) {
            files.push(path);
        }
    }
    Ok(())
}

fn print_table(items: &[ParsedItem]) {
    println!("--- P A R S E   R E S U L T S ---");
    println!(
        "{:<12} | {:<30} | {:>4}:{:<3} | Summary",
        "Rule", "Module", "Line", "Col"
    );
    for item in items {
        let summary = item
            .signature
            .as_deref()
            .or(item.name.as_deref())
            .or(item.docstring.as_deref())
            .unwrap_or(&item.content);
        let module = item
            .module
            .as_deref()
            .or(item.source.as_deref())
            .unwrap_or("-");
        println!(
            "{:<12} | {:<30} | {:>4}:{:<3} | {}",
            item.rule,
            truncate(module, 30),
            item.line,
            item.column,
            summary
        );
    }
}

fn print_json(items: &[ParsedItem]) -> Result<()> {
    let payload = items
        .iter()
        .map(|item| {
            json!({
                "rule": item.rule,
                "module": item.module,
                "source": item.source,
                "name": item.name,
                "signature": item.signature,
                "docstring": item.docstring,
                "line": item.line,
                "column": item.column,
                "content": item.content,
            })
        })
        .collect::<Vec<_>>();
    println!("{}", serde_json::to_string_pretty(&payload)?);
    Ok(())
}

fn truncate(text: &str, max: usize) -> String {
    let char_count = text.chars().count();
    if char_count <= max {
        return text.to_string();
    }
    let trimmed: String = text.chars().take(max.saturating_sub(1)).collect();
    format!("{trimmed}…")
}

fn module_name_from_path(file: &Path, root: &Path) -> String {
    let rel = file.strip_prefix(root).unwrap_or(file);
    let mut rel_path = rel.to_path_buf();
    if rel_path
        .file_name()
        .map(|name| name == "__init__.py")
        .unwrap_or(false)
    {
        rel_path.pop();
    }

    let mut components: Vec<String> = rel_path
        .iter()
        .map(|part| part.to_string_lossy().to_string())
        .collect();

    if let Some(last) = components.last_mut()
        && last.ends_with(".py")
    {
        *last = last.trim_end_matches(".py").to_string();
    }

    components.retain(|segment| !segment.is_empty());
    if components.is_empty() {
        return file
            .parent()
            .and_then(|parent| parent.strip_prefix(root).ok())
            .map(|parent_rel| {
                parent_rel
                    .iter()
                    .map(|p| p.to_string_lossy().to_string())
                    .collect::<Vec<_>>()
                    .join(".")
            })
            .filter(|s| !s.is_empty())
            .or_else(|| file.file_stem().map(|s| s.to_string_lossy().to_string()))
            .unwrap_or_else(|| file.display().to_string());
    }

    components.join(".")
}

fn to_markdown(files: &[PathBuf], module_root: &Path, output: &Path) -> Result<Vec<ParsedItem>> {
    let items = parse_python_files(files, module_root)?;
    let sections = generate_sections(&items);
    let (gemini_request, truncation_warning) = build_llm_request(&items);
    if let Some(note) = &truncation_warning {
        eprintln!("Warning: {note}");
    }
    let summary = RealGeminiClient::new()
        .and_then(|client| client.generate_section(&gemini_request))
        .unwrap_or_else(|err| {
            eprintln!("Warning: Gemini summary unavailable ({err})");
            "Summary unavailable because the Gemini client could not be reached.".to_string()
        });

    let mut content = String::new();
    content.push_str("# Generated README Draft\n\n");
    content.push_str(&format!("{summary}\n\n"));
    content.push_str(&sections.overview);
    content.push('\n');
    content.push_str(&sections.api_table);
    content.push('\n');
    content.push_str(&sections.docstring_coverage);

    fs::write(output, content).with_context(|| format!("Failed to write {}", output.display()))?;
    Ok(items)
}

fn build_llm_request(items: &[ParsedItem]) -> (GeminiRequest, Option<String>) {
    let modules = aggregate_modules(items);
    let (modules_json, included_modules, truncation_warning) = modules_json_for_llm(&modules);
    let docstring_rows = docstring_rows_for_llm(&modules, &included_modules);
    let totals = json!({
        "module_count": modules.len(),
        "functions": modules.values().map(|m| m.functions.len()).sum::<usize>(),
        "classes": modules.values().map(|m| m.classes.len()).sum::<usize>(),
        "docstrings": modules.values().map(|m| m.docstrings).sum::<usize>(),
        "imports": modules.values().map(|m| m.imports).sum::<usize>(),
    });
    let notes_for_payload = truncation_warning.clone();
    let payload = json!({
        "summary": totals,
        "modules": modules_json,
        "docstring_coverage": docstring_rows,
        "notes": notes_for_payload,
    });
    let instructions = "You are helping to draft a README introduction. \
Use the JSON data to describe the project in <=80 words, referencing the most important modules, \
classes vs. functions, and docstring coverage. If documentation looks sparse, mention it.";
    (
        GeminiRequest::new(instructions, payload),
        truncation_warning,
    )
}

fn modules_json_for_llm(
    modules: &BTreeMap<String, ModuleReport>,
) -> (Vec<Value>, Vec<String>, Option<String>) {
    if modules.is_empty() {
        return (Vec::new(), Vec::new(), None);
    }
    let mut rows = Vec::new();
    let mut included = Vec::new();
    let mut notes = Vec::new();
    for (idx, (name, report)) in modules.iter().enumerate() {
        if idx >= MAX_LLM_MODULES {
            notes.push(format!(
                "Only the first {MAX_LLM_MODULES} module(s) were shared with Gemini out of {}.",
                modules.len()
            ));
            break;
        }
        included.push(name.clone());
        let (functions, func_truncated) = symbol_list_for_llm(&report.functions);
        if func_truncated {
            notes.push(format!(
                "Module {name}: only the first {MAX_LLM_SYMBOLS_PER_KIND} function(s) \
were provided out of {}.",
                report.functions.len()
            ));
        }
        let (classes, class_truncated) = symbol_list_for_llm(&report.classes);
        if class_truncated {
            notes.push(format!(
                "Module {name}: only the first {MAX_LLM_SYMBOLS_PER_KIND} class(es) \
were provided out of {}.",
                report.classes.len()
            ));
        }
        rows.push(json!({
            "module": name,
            "functions": functions,
            "classes": classes,
            "docstrings": report.docstrings,
            "imports": report.imports,
        }));
    }
    let note = if notes.is_empty() {
        None
    } else {
        Some(notes.join(" "))
    };
    (rows, included, note)
}

fn symbol_list_for_llm(entries: &[SymbolEntry]) -> (Vec<Value>, bool) {
    let mut rows = Vec::new();
    for entry in entries.iter().take(MAX_LLM_SYMBOLS_PER_KIND) {
        rows.push(symbol_snapshot(entry));
    }
    (rows, entries.len() > MAX_LLM_SYMBOLS_PER_KIND)
}

fn symbol_snapshot(entry: &SymbolEntry) -> Value {
    json!({
        "name": entry.name,
        "signature": entry.signature,
        "location": entry
            .source
            .as_ref()
            .map(|src| format!("{src}:{}", entry.line))
            .unwrap_or_else(|| format!("line {}", entry.line)),
    })
}

fn docstring_rows_for_llm(
    modules: &BTreeMap<String, ModuleReport>,
    included_modules: &[String],
) -> Vec<Value> {
    included_modules
        .iter()
        .filter_map(|module| modules.get(module).map(|report| (module, report)))
        .map(|(module, report)| {
            json!({
                "module": module,
                "functions": report.functions.len(),
                "classes": report.classes.len(),
                "docstrings": report.docstrings,
            })
        })
        .collect()
}

fn autodetect_module_root(path: &Path) -> Option<PathBuf> {
    if path.is_dir() {
        return Some(path.to_path_buf());
    }
    let mut current = path.parent()?;
    loop {
        if project_marker_present(current) {
            return Some(current.to_path_buf());
        }
        match current.parent() {
            Some(parent) => current = parent,
            None => break,
        }
    }
    path.parent().map(PathBuf::from)
}

fn project_marker_present(path: &Path) -> bool {
    path.join("pyproject.toml").is_file()
        || path.join("setup.cfg").is_file()
        || path.join(".git").is_dir()
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyscription::parser::GrammarRule;

    fn make_item(rule: GrammarRule, module: &str, name: &str) -> ParsedItem {
        ParsedItem {
            rule,
            name: Some(name.to_string()),
            signature: Some(match rule {
                GrammarRule::FunctionDef => format!("def {name}()"),
                GrammarRule::ClassDef => format!("class {name}:"),
                _ => name.to_string(),
            }),
            docstring: None,
            content: name.to_string(),
            line: 1,
            column: 1,
            module: Some(module.to_string()),
            source: Some(format!("{module}.py")),
        }
    }

    #[test]
    fn llm_request_is_limited_and_warns_when_truncated() {
        let mut items = Vec::new();
        for idx in 0..(MAX_LLM_MODULES + 2) {
            let module = format!("pkg{idx}");
            items.push(make_item(GrammarRule::FunctionDef, &module, "foo"));
            items.push(make_item(GrammarRule::ClassDef, &module, "Widget"));
        }
        let (request, warning) = build_llm_request(&items);
        let modules_json = request
            .payload_json
            .get("modules")
            .and_then(|value| value.as_array())
            .expect("modules array missing");
        assert!(modules_json.len() <= MAX_LLM_MODULES);
        assert!(warning.is_some());
    }

    #[test]
    fn llm_request_without_truncation_has_no_warning() {
        let items = vec![
            make_item(GrammarRule::FunctionDef, "pkg.core", "foo"),
            make_item(GrammarRule::ClassDef, "pkg.core", "Widget"),
        ];
        let (_, warning) = build_llm_request(&items);
        assert!(warning.is_none());
    }
}
