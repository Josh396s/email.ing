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
    
    # Analyze text to find PII entities
    results = analyzer.analyze(text=text, entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"], language='en')
    pii_map = {}
    
    # Sort results in reverse order to avoid messing up indices when replacing
    sorted_results = sorted(results, key=lambda x: x.start, reverse=True)
    temp_text = text
    
    # Replace each detected entity with a placeholder and store the mapping
    for i, res in enumerate(sorted_results):
        original_value = text[res.start:res.end]
        placeholder = f"<{res.entity_type}_{i}>"
        pii_map[placeholder] = original_value
        
        # Replace the original value with the placeholder in the text
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