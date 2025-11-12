use thiserror::Error;

/// Errors that can surface while normalizing and parsing Python sources.
#[derive(Error, Debug)]
pub enum ParserError {
    /// The provided content was blank after trimming whitespace.
    #[error("File contetnt is empty, nothing to parse")]
    EmptyContent,

    /// A triple-quoted literal was opened but never closed.
    #[error("Docstring starting at line {0} is missing a closing triple quote")]
    UnterminatedDocstring(usize),

    /// The pest parser failed with an unrecoverable syntax error.
    #[error("Syntax error while parsing: {0}")]
    SyntaxError(String),

    /// IO errors propagated while reading files from disk.
    #[error("Failed to read file: {0}")]
    IoError(#[from] std::io::Error),
}
