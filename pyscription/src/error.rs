use thiserror::Error;

#[derive(Error, Debug)]
pub enum ParserError {
    #[error("File contetnt is empty, nothing to parse")]
    EmptyContent,

    #[error("Docstring starting at line {0} is missing a closing triple quote")]
    UnterminatedDocstring(usize),

    #[error("Syntax error while parsing: {0}")]
    SyntaxError(String),

    #[error("Failed to read file: {0}")]
    IoError(#[from] std::io::Error),
}
