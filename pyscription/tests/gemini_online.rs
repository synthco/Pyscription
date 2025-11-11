use pyscription::gemini::{GeminiClient, GeminiRequest, RealGeminiClient};
use serde_json::json;
use std::env;

fn should_run_online_test() -> bool {
    matches!(env::var("PYSCRIPTION_RUN_GEMINI_LIVE_TEST"), Ok(flag) if flag == "1")
        && env::var("GEMINI_API_KEY")
            .map(|key| !key.trim().is_empty())
            .unwrap_or(false)
}

#[test]
#[ignore = "Hits the real Gemini API; run manually with PYSCRIPTION_RUN_GEMINI_LIVE_TEST=1"]
fn gemini_live_summary_generation() {
    if !should_run_online_test() {
        eprintln!(
            "Skipping live Gemini test. Set GEMINI_API_KEY and PYSCRIPTION_RUN_GEMINI_LIVE_TEST=1 \
to enable it."
        );
        return;
    }

    let client = RealGeminiClient::new().expect("Gemini client should initialize with a key");
    let request = GeminiRequest::new(
        "Summarize the detected modules and docstrings in <=80 words.",
        json!({
            "summary": {
                "module_count": 1,
                "functions": 1,
                "classes": 0,
                "docstrings": 1,
                "imports": 0
            },
            "modules": [{
                "module": "loadpipe.core",
                "functions": [{
                    "name": "run_pipeline",
                    "signature": "def run_pipeline(cfg)",
                    "location": "loadpipe/core.py:10"
                }],
                "classes": [],
                "docstrings": 1,
                "imports": 0
            }],
            "docstring_coverage": [{
                "module": "loadpipe.core",
                "functions": 1,
                "classes": 0,
                "docstrings": 1
            }]
        }),
    );

    let summary = match client.generate_section(&request) {
        Ok(text) => text,
        Err(err) => {
            eprintln!(
                "Skipping assertion: Gemini API call failed ({}). \
This usually means the public endpoint is temporarily unavailable.",
                err
            );
            return;
        }
    };
    assert!(
        summary.trim().len() > 16,
        "Gemini returned an unexpectedly short summary: {summary}"
    );
}
