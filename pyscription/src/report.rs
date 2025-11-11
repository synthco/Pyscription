use crate::parser::{GrammarRule, ParsedItem};
use std::collections::BTreeMap;

/// Aggregated information for a single Python module.
#[derive(Debug, Default, Clone)]
pub struct ModuleReport {
    pub functions: Vec<SymbolEntry>,
    pub classes: Vec<SymbolEntry>,
    pub docstrings: usize,
    pub imports: usize,
}

/// Basic metadata about a function or class emitted by the parser.
#[derive(Debug, Clone)]
pub struct SymbolEntry {
    pub name: String,
    pub signature: String,
    pub line: usize,
    pub source: Option<String>,
}

/// Group parser items by module so downstream renderers can reuse the same snapshot.
pub fn aggregate_modules(items: &[ParsedItem]) -> BTreeMap<String, ModuleReport> {
    let mut modules = BTreeMap::new();
    for item in items {
        let module_name = module_key(item);
        let report = modules
            .entry(module_name)
            .or_insert_with(ModuleReport::default);
        match item.rule {
            GrammarRule::FunctionDef => report.functions.push(SymbolEntry::from_item(item)),
            GrammarRule::ClassDef => report.classes.push(SymbolEntry::from_item(item)),
            GrammarRule::Docstring => report.docstrings += 1,
            GrammarRule::Import => report.imports += 1,
        }
    }
    for report in modules.values_mut() {
        report
            .functions
            .sort_by(|a, b| a.name.to_lowercase().cmp(&b.name.to_lowercase()));
        report
            .classes
            .sort_by(|a, b| a.name.to_lowercase().cmp(&b.name.to_lowercase()));
    }
    modules
}

impl SymbolEntry {
    fn from_item(item: &ParsedItem) -> Self {
        Self {
            name: item
                .name
                .clone()
                .unwrap_or_else(|| "<anonymous>".to_string()),
            signature: item
                .signature
                .clone()
                .unwrap_or_else(|| item.content.clone()),
            line: item.line,
            source: item.source.clone(),
        }
    }
}

fn module_key(item: &ParsedItem) -> String {
    item.module
        .clone()
        .or_else(|| item.source.clone())
        .unwrap_or_else(|| "<unknown>".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

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
    fn aggregator_groups_items() {
        let items = vec![
            make_item(GrammarRule::FunctionDef, "pkg", "foo", "def foo()"),
            make_item(GrammarRule::ClassDef, "pkg", "Bar", "class Bar"),
            make_item(GrammarRule::Import, "pkg", "", "import os"),
        ];
        let modules = aggregate_modules(&items);
        let pkg = modules.get("pkg").expect("pkg module missing");
        assert_eq!(pkg.functions.len(), 1);
        assert_eq!(pkg.classes.len(), 1);
        assert_eq!(pkg.imports, 1);
    }
}
