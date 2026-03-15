import os
import time
import logging

import google.generativeai as genai

log = logging.getLogger(__name__)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Temperature settings for different use cases
VERIFIER_TEMP = float(os.environ.get("GEMINI_VERIFIER_TEMPERATURE", "0.2"))  # Deterministic
AGENT_TEMPS = {
    "beginner": float(os.environ.get("GEMINI_BEGINNER_TEMPERATURE", "1.0")),      # High variation
    "intermediate": float(os.environ.get("GEMINI_INTERMEDIATE_TEMPERATURE", "0.7")),  # Moderate
    "expert": float(os.environ.get("GEMINI_EXPERT_TEMPERATURE", "0.3")),          # Low variation
}

MAX_TOKENS = int(os.environ.get("GEMINI_MAX_TOKENS", "1000"))
TOP_P = float(os.environ.get("GEMINI_TOP_P", "1"))
TOP_K = int(os.environ.get("GEMINI_TOP_K", "1"))

_base_model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite"))


def _call_with_retries(func, *args, max_retries=3, **kwargs):
    """Call a function with exponential backoff retry (max 3 retries)."""
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries:
                raise
            wait_time = 2 ** attempt
            log.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)


def generate_content(prompt: str, temperature: float | None = None) -> object:
    """Generate content with optional custom temperature."""
    if temperature is None:
        temperature = VERIFIER_TEMP
    
    config = genai.GenerationConfig(
        temperature=temperature,
        top_p=TOP_P,
        top_k=TOP_K,
        max_output_tokens=MAX_TOKENS,
    )
    return _call_with_retries(_base_model.generate_content, prompt, generation_config=config)


class ModelInterface:
    """Simple interface matching the old ModelWrapper for compatibility."""
    
    def generate_content(self, prompt: str, **kwargs):
        # Use verifier temperature by default
        return generate_content(prompt, temperature=VERIFIER_TEMP)


model = ModelInterface()