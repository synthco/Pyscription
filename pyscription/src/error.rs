use thiserror::Error;

#[derive(Error, Debug)]
pub enum  ParserError {
    #[error("File contetnt is empty, nothing to parse")]
    EmptyContent,

    #[error("Failed to read file: {0}")]
    IoError(#[from] std::io::Error)
}
