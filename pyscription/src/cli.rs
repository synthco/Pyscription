use clap::{Parser, Subcommand, ValueEnum};
#[derive(Parser, Debug)]
#[command(
    version,
    about = "Pyscription CLI – pest-powered parser driving token-efficient README generation"
)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand, Debug)]
pub enum Commands {
    Parse {
        /// File or directory to analyze
        #[arg(value_name = "PATH")]
        path: String,
        /// Output format for parse results
        #[arg(
            short,
            long,
            value_enum,
            default_value_t = OutputFormat::Table,
            help = "Presentation format for parse results"
        )]
        format: OutputFormat,
        /// Optional override for the module root
        #[arg(long, value_name = "DIR", help = "Explicit module root override")]
        module_root: Option<String>,
        /// Optional path to render Markdown output that includes a Gemini-generated summary
        #[arg(
            long,
            value_name = "FILE",
            help = "Write README-ready Markdown to this file"
        )]
        markdown: Option<String>,
    },
    Credits,
}

#[derive(ValueEnum, Debug, Clone, Copy)]
pub enum OutputFormat {
    Table,
    Json,
}
