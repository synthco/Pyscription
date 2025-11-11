use crate::parser::ParsedItem;
use crate::report::{ModuleReport, SymbolEntry, aggregate_modules};
use std::collections::BTreeMap;

/// Rendered deterministic sections ready to be embedded into README.md.
#[derive(Debug, Clone)]
pub struct GeneratedSections {
    pub overview: String,
    pub api_table: String,
    pub docstring_coverage: String,
}

/// Build the Overview/API/Docstring sections by grouping pest-derived items per module.
pub fn generate_sections(items: &[ParsedItem]) -> GeneratedSections {
    let modules = aggregate_modules(items);
    let overview = render_overview(&modules);
    let api_table = render_api_tables(&modules);
    let docstring_coverage = render_docstring_coverage(&modules);

    GeneratedSections {
        overview,
        api_table,
        docstring_coverage,
    }
}

fn render_overview(modules: &BTreeMap<String, ModuleReport>) -> String {
    let module_count = modules.len();
    let total_functions: usize = modules.values().map(|m| m.functions.len()).sum();
    let total_classes: usize = modules.values().map(|m| m.classes.len()).sum();
    let total_docstrings: usize = modules.values().map(|m| m.docstrings).sum();
    let total_imports: usize = modules.values().map(|m| m.imports).sum();

    format!(
        "## Overview\n\
Detected **{module_count}** module(s), **{total_functions}** function(s), \
**{total_classes}** class(es), and **{total_docstrings}** docstring(s). The code references \
**{total_imports}** imports.\n\n"
    )
}

fn render_api_tables(modules: &BTreeMap<String, ModuleReport>) -> String {
    if modules.is_empty() {
        return "## API Reference\n_No modules discovered._\n".to_string();
    }

    let mut out = String::from("## API Reference\n");
    for (module, report) in modules {
        out.push_str(&format!("\n### Module `{}`\n", module));
        if report.functions.is_empty() && report.classes.is_empty() {
            out.push_str("_No functions or classes detected in this module._\n");
            continue;
        }
        if !report.functions.is_empty() {
            out.push_str("| Function | Signature | Location |\n");
            out.push_str("| --- | --- | --- |\n");
            for function in &report.functions {
                let location = entry_location(function);
                out.push_str(&format!(
                    "| `{}` | `{}` | `{}` |\n",
                    function.name, function.signature, location
                ));
            }
        }
        if !report.classes.is_empty() {
            if !report.functions.is_empty() {
                out.push('\n');
            }
            out.push_str("| Class | Signature | Location |\n");
            out.push_str("| --- | --- | --- |\n");
            for class in &report.classes {
                let location = entry_location(class);
                out.push_str(&format!(
                    "| `{}` | `{}` | `{}` |\n",
                    class.name, class.signature, location
                ));
            }
        }
    }
    out
}

fn render_docstring_coverage(modules: &BTreeMap<String, ModuleReport>) -> String {
    if modules.is_empty() {
        return "## Docstring Coverage\n_No modules discovered._\n".to_string();
    }

    let mut out = String::from(
        "## Docstring Coverage\n\n| Module | Functions | Classes | Docstrings | Coverage |\n| --- | ---:| ---:| ---:| ---:|\n",
    );
    for (module, report) in modules {
        let func_count = report.functions.len();
        let class_count = report.classes.len();
        let doc_count = report.docstrings;
        let total_symbols = func_count + class_count;
        let coverage = if total_symbols == 0 {
            "N/A".to_string()
        } else {
            let pct = (doc_count.min(total_symbols) as f32 / total_symbols as f32) * 100.0;
            format!("{pct:.0}%")
        };
        out.push_str(&format!(
            "| `{module}` | {} | {} | {} | {} |\n",
            func_count, class_count, doc_count, coverage
        ));
    }
    out
}

fn entry_location(entry: &SymbolEntry) -> String {
    entry
        .source
        .as_ref()
        .map(|src| format!("{src}:{}", entry.line))
        .unwrap_or_else(|| format!("line {}", entry.line))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parser::GrammarRule;

    fn make_item(rule: GrammarRule, module: &str, name: &str, signature: &str) -> ParsedItem {
        ParsedItem {
            rule,
            name: if name.is_empty() {
                None
            } else {
                Some(name.to_string())
            },
            signature: if signature.is_empty() {
                None
            } else {
                Some(signature.to_string())
            },
            docstring: None,
            content: signature.to_string(),
            line: 1,
            column: 1,
            module: Some(module.to_string()),
            source: Some(format!("{module}.py")),
        }
    }

    #[test]
    fn generator_creates_sections() {
        let items = vec![
            make_item(GrammarRule::FunctionDef, "pkg.utils", "foo", "def foo(x)"),
            make_item(GrammarRule::Docstring, "pkg.utils", "", "\"\"\"doc\"\"\""),
            make_item(GrammarRule::Import, "pkg.utils", "", "import os"),
            make_item(
                GrammarRule::ClassDef,
                "pkg.utils",
                "Widget",
                "class Widget:",
            ),
        ];

        let sections = generate_sections(&items);
        assert!(sections.overview.contains("**1** module"));
        assert!(sections.overview.contains("**1** class"));
        assert!(sections.api_table.contains("Module `pkg.utils`"));
        assert!(sections.api_table.contains("| Class |"));
        assert!(sections.docstring_coverage.contains("pkg.utils"));
    }
}
