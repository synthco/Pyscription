use anyhow::{Context, Result, anyhow};
use reqwest::blocking::Client as HttpClient;
use serde::Deserialize;
use serde_json::{self, Value};
use std::fs;
use std::sync::Mutex;

const DEFAULT_CONFIG_PATH: &str = "src/sercrets.yaml";
const DEFAULT_ENDPOINT: &str =
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent";

// Trait describing the minimal Gemini client surface used by the generator layer.
pub trait GeminiClient: Send + Sync {
    // Produce a textual section (e.g., Introduction/Usage) for the README.
    fn generate_section(&self, request: &GeminiRequest) -> Result<String>;
}

// Placeholder implementation that records the API key location but does not yet perform HTTP calls.
pub struct RealGeminiClient {
    api_key: String,
    endpoint: String,
    http: HttpClient,
}

impl RealGeminiClient {
    /// Load an API key either from `GEMINI_API_KEY` or from `src/sercrets.yaml`.
    pub fn new() -> Result<Self> {
        let key =
            std::env::var("GEMINI_API_KEY").or_else(|_| read_key_from_file(DEFAULT_CONFIG_PATH))?;
        let endpoint =
            std::env::var("GEMINI_API_ENDPOINT").unwrap_or_else(|_| DEFAULT_ENDPOINT.into());
        Ok(Self {
            api_key: key,
            endpoint,
            http: HttpClient::builder()
                .user_agent("pyscription/0.1.0")
                .build()?,
        })
    }
}

impl GeminiClient for RealGeminiClient {
    fn generate_section(&self, request: &GeminiRequest) -> Result<String> {
        let json_text = serde_json::to_string_pretty(&request.payload_json)?;
        let combined = format!(
            "{}\n\n--- BEGIN PARSER JSON ---\n{}\n--- END PARSER JSON ---",
            request.instructions, json_text
        );
        let payload = serde_json::json!({
            "contents": [{
                "parts": [{ "text": combined }]
            }]
        });

        let response = self
            .http
            .post(&self.endpoint)
            .header("x-goog-api-key", &self.api_key)
            .json(&payload)
            .send()
            .with_context(|| "Failed to call Gemini API")?
            .error_for_status()
            .with_context(|| "Gemini API returned an error status")?;

        let parsed: GenerateResponse = response
            .json()
            .with_context(|| "Failed to parse Gemini API response")?;

        parsed
            .primary_text()
            .ok_or_else(|| anyhow!("Gemini API response did not contain any text"))
    }
}

/// In-memory mock used in unit/integration tests to keep the suite offline
#[derive(Default)]
pub struct MockGeminiClient {
    responses: Mutex<Vec<String>>,
}

impl MockGeminiClient {
    pub fn with_responses(responses: Vec<String>) -> Self {
        Self {
            responses: Mutex::new(responses),
        }
    }
}

impl GeminiClient for MockGeminiClient {
    fn generate_section(&self, request: &GeminiRequest) -> Result<String> {
        let mut guard = self.responses.lock().expect("mock mutex poisoned");
        if guard.is_empty() {
            Ok(format!("MOCK_RESPONSE::{}", request.instructions))
        } else {
            Ok(guard.remove(0))
        }
    }
}

/// Structured prompt data shared with Gemini so instructions and JSON stay separate.
#[derive(Debug, Clone)]
pub struct GeminiRequest {
    pub instructions: String,
    pub payload_json: Value,
}

impl GeminiRequest {
    pub fn new(instructions: impl Into<String>, payload_json: Value) -> Self {
        Self {
            instructions: instructions.into(),
            payload_json,
        }
    }
}

fn read_key_from_file(path: &str) -> Result<String> {
    let contents = fs::read_to_string(path)
        .with_context(|| format!("Failed to read Gemini secrets file at {path}"))?;
    contents
        .lines()
        .find_map(|line| line.trim().strip_prefix("key:").map(str::trim))
        .map(|value| value.trim_matches('"').to_string())
        .filter(|value| !value.is_empty() && value != "REPLACE_ME")
        .ok_or_else(|| {
            anyhow!(
                "Gemini API key not found in {path}. Set GEMINI_API_KEY or update sercrets.yaml"
            )
        })
}

#[derive(Debug, Deserialize)]
struct GenerateResponse {
    #[serde(default)]
    candidates: Vec<Candidate>,
}

#[derive(Debug, Deserialize)]
struct Candidate {
    #[serde(default)]
    content: Option<CandidateContent>,
}

#[derive(Debug, Deserialize)]
struct CandidateContent {
    #[serde(default)]
    parts: Vec<ContentPart>,
}

#[derive(Debug, Deserialize)]
struct ContentPart {
    #[serde(default)]
    text: Option<String>,
}

impl GenerateResponse {
    fn primary_text(&self) -> Option<String> {
        self.candidates
            .iter()
            .find_map(|candidate| candidate.content.as_ref())
            .and_then(|content| {
                content
                    .parts
                    .iter()
                    .find_map(|part| part.text.as_ref())
                    .cloned()
            })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mock_returns_seeded_response() {
        let mock = MockGeminiClient::with_responses(vec!["hello world".into()]);
        let first = mock
            .generate_section(&GeminiRequest::new("prompt", serde_json::json!({})))
            .unwrap();
        assert_eq!(first, "hello world");
        let fallback = mock
            .generate_section(&GeminiRequest::new("prompt2", serde_json::json!({})))
            .unwrap();
        assert_eq!(fallback, "MOCK_RESPONSE::prompt2");
    }
}
