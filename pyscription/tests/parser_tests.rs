use pyscription::error::ParserError;
use pyscription::parser::{GrammarRule, parse_content};

#[test]
fn test_parse_content_extracts_items() {
    let content = r#"
def foo():
    pass

"""module level doc"""
"#;

    let parsed = parse_content(content).expect("failed to parse content");

    assert_eq!(parsed.len(), 2);
    let func = parsed
        .iter()
        .find(|item| item.rule == GrammarRule::FunctionDef)
        .expect("function missing");
    assert_eq!(func.name.as_deref(), Some("foo"));
    assert_eq!(func.signature.as_deref(), Some("def foo():"));
    assert_eq!(func.line, 2);
    assert_eq!(func.column, 1);

    let doc = parsed
        .iter()
        .find(|item| item.rule == GrammarRule::Docstring)
        .expect("docstring missing");
    assert_eq!(doc.docstring.as_deref(), Some("module level doc"));
    assert_eq!(doc.line, 5);
}

#[test]
fn test_parse_content_empty_error() {
    let err = parse_content("").expect_err("expected empty content error");

    assert!(matches!(err, ParserError::EmptyContent));
}

#[test]
fn test_parse_content_parses_example_file() {
    let content = include_str!("examples/download.py");
    let parsed = parse_content(content).expect("failed to parse example content");
    assert!(parsed.iter().any(|item| item.rule == GrammarRule::Import));

    let fn_item = parsed
        .iter()
        .find(|item| {
            item.rule == GrammarRule::FunctionDef && item.name.as_deref() == Some("download_iter")
        })
        .expect("download_iter not found");
    assert_eq!(fn_item.signature.as_deref(), Some("def download_iter("));

    let doc_entry = parsed
        .iter()
        .find(|item| item.rule == GrammarRule::Docstring)
        .expect("docstring entry missing");
    assert!(
        doc_entry
            .docstring
            .as_deref()
            .expect("docstring text missing")
            .starts_with("Stream file content from Google Drive")
    );

    let nested_fn = parsed
        .iter()
        .find(|item| {
            item.rule == GrammarRule::FunctionDef && item.name.as_deref() == Some("_stream")
        })
        .expect("nested function not found");
    assert_eq!(
        nested_fn.signature.as_deref().expect("signature missing"),
        "def _stream() -> Iterator[bytes]:"
    );
}

#[test]
fn test_parse_content_reports_unterminated_docstring() {
    let err = parse_content(
        r#"
"""still open
def foo():
    pass
"#,
    )
    .expect_err("expected unterminated docstring");

    assert!(matches!(err, ParserError::UnterminatedDocstring(2)));
}

#[test]
fn test_parse_content_normalizes_multiline_docstring() {
    let content = r#"
def foo():
    pass

"""
    Summary line

        Details with indent
"""
"#;

    let parsed = parse_content(content).expect("parse failed");
    let doc = parsed
        .iter()
        .find(|item| item.rule == GrammarRule::Docstring)
        .expect("docstring missing");
    assert_eq!(
        doc.docstring.as_deref(),
        Some("Summary line\n\nDetails with indent")
    );
}

#[test]
fn test_parse_content_identifies_imports() {
    let content = r#"
import os
from collections import deque
"#;

    let parsed = parse_content(content).expect("parse failed");
    let has_plain = parsed
        .iter()
        .any(|item| item.rule == GrammarRule::Import && item.content.starts_with("import "));
    let has_from = parsed
        .iter()
        .any(|item| item.rule == GrammarRule::Import && item.content.starts_with("from "));
    assert!(has_plain && has_from);
}

#[test]
fn test_parse_content_ignores_text_without_rules() {
    let content = r#"
print("nothing to see here")

"import foo"  # string literal
"#;

    let parsed = parse_content(content).expect("parse failed");
    assert!(!parsed.iter().any(|item| item.rule == GrammarRule::Import));
    assert!(
        !parsed
            .iter()
            .any(|item| item.rule == GrammarRule::FunctionDef)
    );
}

#[test]
fn test_parse_content_identifies_classes() {
    let content = r#"
@decorator
class Widget(Base):
    pass
"#;

    let parsed = parse_content(content).expect("parse failed");
    let class_item = parsed
        .iter()
        .find(|item| item.rule == GrammarRule::ClassDef)
        .expect("class definition missing");
    assert_eq!(class_item.name.as_deref(), Some("Widget"));
    assert_eq!(class_item.signature.as_deref(), Some("class Widget(Base):"));
    assert_eq!(class_item.line, 2);
}
