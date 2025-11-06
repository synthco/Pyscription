use clap::{Parser, Subcommand};
#[derive(Parser, Debug)]
#[command(version, about)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand, Debug)]
pub enum Commands {
    Parse {
        #[arg(required = true)]
        file_path: String,
    },
    Credits,
}