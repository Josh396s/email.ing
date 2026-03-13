import re
import logging
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)

# Utilize smaller spacy model for lower latency in masking/unmasking
nlp_config = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}
provider = NlpEngineProvider(nlp_configuration=nlp_config)
nlp_engine = provider.create_engine()

# Initialize Presidio Analyzer
analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

def mask_content(text: str):
    '''
    Mask PII in the text and create a mapping of placeholders to original values
    '''
    if not text:
        return "", {}

    # Set analyzer with these settings
    results = analyzer.analyze(
        text=text,
        entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"],
        language='en'
    )

    # Sort in reverse order to preserve correct indices during replacement
    sorted_results = sorted(results, key=lambda x: x.start, reverse=True)

    pii_map = {}
    temp_text = text
    entity_counters = {}

    for res in sorted_results:
        entity_type = res.entity_type
        original_value = text[res.start:res.end].strip()

        # Skip empty or single-character matches (Presidio noise)
        if len(original_value) <= 1:
            continue

        # Check if this exact value was already masked (deduplication)
        existing = next((k for k, v in pii_map.items() if v == original_value), None)
        if existing:
            # Reuse the same placeholder for the same value
            temp_text = temp_text[:res.start] + existing + temp_text[res.end:]
            continue

        # Assign a new placeholder with per-type counter
        count = entity_counters.get(entity_type, 0)
        placeholder = f"<{entity_type}_{count}>"
        entity_counters[entity_type] = count + 1

        pii_map[placeholder] = original_value
        temp_text = temp_text[:res.start] + placeholder + temp_text[res.end:]

    return temp_text, pii_map

def deanonymize_text(text: str, pii_map: dict) -> str:
    '''
    Unmask PII in the text
    '''
    if not text or not pii_map:
        return text
    
    for placeholder, real_value in pii_map.items():
        text = text.replace(placeholder, real_value)
    return text