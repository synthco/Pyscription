use pyscription::error::ParserError;
use pyscription::parser::{parse_content, ParsedItem};

#[test]
fn test_parse_content_extracts_items() {
    let content = r#"
def foo():
    pass

"""module level doc"""
"#;

    let parsed = parse_content(content).expect("failed to parse content");

    assert_eq!(parsed.len(), 2);
    assert_eq!(
        parsed[0],
        ParsedItem {
            item_type: "Function".to_string(),
            content: "def foo():".to_string(),
        }
    );
    assert_eq!(
        parsed[1],
        ParsedItem {
            item_type: "Docstring".to_string(),
            content: "\"\"\"module level doc\"\"\"".to_string(),
        }
    );
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
    assert_eq!(parsed.len(), 5);
    assert_eq!(parsed[0].item_type, "Function");
    assert_eq!(parsed[0].content, "def download_iter(");
    assert_eq!(parsed[1].item_type, "Docstring");
    assert_eq!(parsed[1].content, "\"\"\"");
    assert_eq!(parsed[2].item_type, "Docstring");
    assert_eq!(parsed[2].content, "\"\"\"");
    assert_eq!(parsed[3].item_type, "Function");
    assert_eq!(parsed[3].content, "def _stream() -> Iterator[bytes]:");
    assert_eq!(parsed[4].item_type, "Function");
    assert_eq!(parsed[4].content, "def _cache_reader() -> Iterator[bytes]:");
}
