mod cli;
use anyhow::Result;
use clap::Parser;
use std::fs;
use std::process;

// use pyscription::{parser, error::ParserError};
use cli::{Cli, Commands};
use pyscription::parser::parse_content;

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Parse { file_path } => {
            if let Err(e) = run_parese(&file_path) {
                eprintln!("Error: {}", e);
                process::exit(1);
            }
        }
        Commands::Credits => { println!("Made by Ivan Tyshchenko"); }
    }
    Ok(())
}

fn run_parese(file_path: &str) -> Result<()> {
    let content = fs::read_to_string(file_path)?;
    let items = parse_content(&content)?;
    println!("--- P A R S E   R E S U L T S ---");
    for item in items {
        println!("{}: {}", item.item_type, item.content);
    }
    Ok(())
}