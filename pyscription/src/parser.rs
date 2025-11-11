use crate::error::ParserError;
use pest::Parser;
use pest::error::{Error as PestError, ErrorVariant, LineColLocation};
use pest::iterators::Pair;
use pest_derive::Parser;
use serde::Serialize;
use std::fmt;

const DOCSTRING_DELIM: &str = "\"\"\"";

#[derive(Parser)]
#[grammar = "parser.pest"]
struct PyParser;

/// Grammar rules implemented by the parser (mirrors definitions in `parser.pest`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum GrammarRule {
    /// Matches the `function_def` production:
    ///
    /// ```pest
    /// function_def = @{
    ///     decorator_line* ~ indentation? ~ async_prefix? ~ "def" ~ WHITESPACE+ ~ identifier ~ function_signature_tail
    /// }
    /// ```
    ///
    /// This rule emits one `ParsedItem` per Python function and preserves the full signature line.
    FunctionDef,
    /// Matches the `docstring` production:
    ///
    /// ```pest
    /// docstring = @{ indentation? ~ triple_quote ~ docstring_body? ~ triple_quote }
    /// ```
    ///
    /// It captures triple-quoted literals (including indentation) so we can normalize their bodies.
    Docstring,
    /// Matches the `class_def` production:
    ///
    /// ```pest
    /// class_def = @{
    ///     decorator_line* ~ indentation? ~ "class" ~ WHITESPACE+ ~ identifier ~ class_signature_tail
    /// }
    /// ```
    ///
    /// Builds items for every `class` declaration, preserving the declaration line (bases, colon, etc.).
    ClassDef,
    /// Matches the `import_stmt` production:
    ///
    /// ```pest
    /// import_stmt = @{ indentation? ~ (plain_import | from_import) ~ NEWLINE? }
    /// ```
    ///
    /// The parser uses this to emit items for both `import foo` and `from pkg import bar` statements.
    Import,
}

impl fmt::Display for GrammarRule {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            GrammarRule::FunctionDef => write!(f, "FunctionDef"),
            GrammarRule::Docstring => write!(f, "Docstring"),
            GrammarRule::ClassDef => write!(f, "ClassDef"),
            GrammarRule::Import => write!(f, "Import"),
        }
    }
}

/// Parsed representation of a Python artifact detected by the grammar rules.
#[derive(Debug, PartialEq, Eq, Serialize)]
pub struct ParsedItem {
    pub rule: GrammarRule,
    pub name: Option<String>,
    pub signature: Option<String>,
    pub docstring: Option<String>,
    pub content: String,
    pub line: usize,
    pub column: usize,
    pub module: Option<String>,
    pub source: Option<String>,
}

/// Parse Python source code and extract grammar matches for README generation.
pub fn parse_content(content: &str) -> Result<Vec<ParsedItem>, ParserError> {
    if content.trim().is_empty() {
        return Err(ParserError::EmptyContent);
    }

    validate_docstrings(content)?;
    let pairs = PyParser::parse(Rule::program, content).map_err(map_pest_error)?;
    let mut items = Vec::new();

    for pair in pairs {
        collect_items(pair, content, &mut items);
    }

    Ok(items)
}

/// Parse a Python module while annotating every item with the provided module name.
pub fn parse_module(content: &str, module: &str) -> Result<Vec<ParsedItem>, ParserError> {
    let mut items = parse_content(content)?;
    for item in &mut items {
        item.module = Some(module.to_string());
    }
    Ok(items)
}

fn collect_items(pair: Pair<Rule>, source: &str, items: &mut Vec<ParsedItem>) {
    match pair.as_rule() {
        Rule::function_def => items.push(build_function_item(pair, source)),
        Rule::class_def => items.push(build_class_item(pair, source)),
        Rule::docstring => items.push(build_docstring_item(pair, source)),
        Rule::import_stmt => {
            let span = pair.as_span();
            if is_line_start(source, span.start()) {
                items.push(build_import_item(pair, source));
            }
        }
        _ => {
            for inner in pair.into_inner() {
                collect_items(inner, source, items);
            }
        }
    }
}

fn build_function_item(pair: Pair<Rule>, source: &str) -> ParsedItem {
    let span = pair.as_span();
    let (line, column) = byte_to_line_col(source, span.start());
    let block = pair.as_str();
    let signature = extract_signature_line(block);
    let name = extract_name_from_signature(&signature);

    ParsedItem {
        rule: GrammarRule::FunctionDef,
        name,
        signature: if signature.is_empty() {
            None
        } else {
            Some(signature)
        },
        docstring: None,
        content: block.trim().to_string(),
        line,
        column,
        module: None,
        source: None,
    }
}

fn build_class_item(pair: Pair<Rule>, source: &str) -> ParsedItem {
    let span = pair.as_span();
    let (line, column) = byte_to_line_col(source, span.start());
    let block = pair.as_str();
    let signature = extract_class_signature_line(block);
    let name = extract_class_name(&signature);

    ParsedItem {
        rule: GrammarRule::ClassDef,
        name,
        signature: if signature.is_empty() {
            None
        } else {
            Some(signature)
        },
        docstring: None,
        content: block.trim().to_string(),
        line,
        column,
        module: None,
        source: None,
    }
}

fn build_docstring_item(pair: Pair<Rule>, source: &str) -> ParsedItem {
    let span = pair.as_span();
    let (line, column) = byte_to_line_col(source, span.start());
    let literal = pair.as_str();
    let raw = extract_docstring_literal(literal);
    let docstring = normalize_docstring(&raw);

    ParsedItem {
        rule: GrammarRule::Docstring,
        name: None,
        signature: None,
        docstring: Some(docstring),
        content: literal.trim().to_string(),
        line,
        column,
        module: None,
        source: None,
    }
}

fn build_import_item(pair: Pair<Rule>, source: &str) -> ParsedItem {
    let span = pair.as_span();
    let (line, column) = byte_to_line_col(source, span.start());
    let statement = pair.as_str().trim().to_string();
    let name = extract_import_name(&statement);

    ParsedItem {
        rule: GrammarRule::Import,
        name,
        signature: None,
        docstring: None,
        content: statement,
        line,
        column,
        module: None,
        source: None,
    }
}

fn byte_to_line_col(source: &str, byte_offset: usize) -> (usize, usize) {
    let mut line = 1;
    let mut column = 1;
    for (idx, ch) in source.char_indices() {
        if idx == byte_offset {
            break;
        }
        if ch == '\n' {
            line += 1;
            column = 1;
        } else {
            column += 1;
        }
    }
    (line, column)
}

fn normalize_docstring(raw: &str) -> String {
    let trimmed = raw.trim_matches('\n');
    if trimmed.trim().is_empty() {
        return String::new();
    }

    let lines: Vec<&str> = trimmed.lines().collect();
    if lines.len() == 1 {
        return lines[0].trim().to_string();
    }

    let mut min_indent = usize::MAX;
    for line in &lines {
        if line.trim().is_empty() {
            continue;
        }
        let indent = line.chars().take_while(|c| c.is_whitespace()).count();
        if indent < min_indent {
            min_indent = indent;
        }
    }

    if min_indent == usize::MAX {
        return trimmed.to_string();
    }

    lines
        .iter()
        .map(|line| {
            if line.trim().is_empty() {
                String::new()
            } else {
                line.chars()
                    .skip(min_indent)
                    .collect::<String>()
                    .trim()
                    .to_string()
            }
        })
        .collect::<Vec<String>>()
        .join("\n")
        .trim()
        .to_string()
}

fn map_pest_error(err: PestError<Rule>) -> ParserError {
    if let ErrorVariant::ParsingError { positives, .. } = &err.variant
        && positives
            .iter()
            .any(|rule| matches!(rule, Rule::triple_quote | Rule::docstring))
    {
        let line = match &err.line_col {
            LineColLocation::Pos((line, _)) => Some(*line),
            LineColLocation::Span((line, _), _) => Some(*line),
        };
        if let Some(line) = line {
            return ParserError::UnterminatedDocstring(line);
        }
    }
    ParserError::SyntaxError(err.to_string())
}

fn extract_signature_line(block: &str) -> String {
    block
        .lines()
        .find_map(|line| {
            let trimmed = line.trim();
            if trimmed.starts_with("def ") || trimmed.starts_with("async def ") {
                Some(trimmed.to_string())
            } else {
                None
            }
        })
        .unwrap_or_else(|| block.lines().next().unwrap_or("").trim().to_string())
}

fn extract_class_signature_line(block: &str) -> String {
    block
        .lines()
        .find_map(|line| {
            let trimmed = line.trim();
            if trimmed.starts_with("class ") {
                Some(trimmed.to_string())
            } else {
                None
            }
        })
        .unwrap_or_else(|| block.lines().next().unwrap_or("").trim().to_string())
}

fn extract_name_from_signature(signature: &str) -> Option<String> {
    let without_async = signature
        .trim_start()
        .strip_prefix("async ")
        .unwrap_or(signature.trim_start());
    let after_def = without_async.strip_prefix("def ")?;
    let name_part = after_def.split('(').next()?.trim();
    if name_part.is_empty() {
        None
    } else {
        Some(name_part.to_string())
    }
}

fn extract_class_name(signature: &str) -> Option<String> {
    let after_class = signature.trim_start().strip_prefix("class ")?;
    let name_part = after_class
        .split(|c: char| c == '(' || c == ':' || c.is_whitespace())
        .find(|segment| !segment.is_empty())?
        .trim();
    if name_part.is_empty() {
        None
    } else {
        Some(name_part.to_string())
    }
}

fn extract_docstring_literal(literal: &str) -> String {
    let trimmed = literal.trim_start();
    if let Some(start) = trimmed.find(DOCSTRING_DELIM) {
        let after_start = start + DOCSTRING_DELIM.len();
        if let Some(end_rel) = trimmed[after_start..].rfind(DOCSTRING_DELIM) {
            let end = after_start + end_rel;
            return trimmed[after_start..end].to_string();
        }
    }
    String::new()
}

fn extract_import_name(statement: &str) -> Option<String> {
    let normalized = statement.lines().next().unwrap_or("").trim();
    if normalized.is_empty() {
        return None;
    }
    Some(normalized.to_string())
}

fn validate_docstrings(content: &str) -> Result<(), ParserError> {
    let mut index = 0;
    while let Some(rel) = content[index..].find(DOCSTRING_DELIM) {
        let start = index + rel;
        let search_from = start + DOCSTRING_DELIM.len();
        if let Some(end_rel) = content[search_from..].find(DOCSTRING_DELIM) {
            index = search_from + end_rel + DOCSTRING_DELIM.len();
        } else {
            let (line, _) = byte_to_line_col(content, start);
            return Err(ParserError::UnterminatedDocstring(line));
        }
    }
    Ok(())
}

fn is_line_start(source: &str, offset: usize) -> bool {
    if offset == 0 {
        return true;
    }
    source[..offset]
        .chars()
        .last()
        .map(|ch| ch == '\n' || ch == '\r')
        .unwrap_or(true)
}
