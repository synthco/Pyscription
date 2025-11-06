use crate::error::ParserError;

#[derive(Debug, PartialEq)]
pub struct ParsedItem {
    pub item_type: String,
    pub content: String,
}

pub fn parse_content(content: &str) -> Result<Vec<ParsedItem>, ParserError>{
    if content.is_empty() {
        return Err(ParserError::EmptyContent);
    }
    let mut results = Vec::new();
    for line in content.lines() {
        let trimmed_line = line.trim();
        if trimmed_line.starts_with("def ") {
            results.push(ParsedItem {
                item_type: "Function".to_string(),
                content: trimmed_line.to_string(),
            });
        }
        else if trimmed_line.starts_with("\"\"\"") {
            results.push(ParsedItem {
                item_type: "Docstring".to_string(),
                content: trimmed_line.to_string(),
            });
        }
    }
    Ok(results)
}