import logging
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)

# Utilize smaller spacy model for lower latency in masking/unmasking
nlp_config = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}
provider = NlpEngineProvider(nlp_configuration=nlp_config)
nlp_engine = provider.create_engine()

# Initialize Presidio Analyzer and Anonymizer
analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
anonymizer = AnonymizerEngine()

def mask_content(text: str):
    '''
    Mask PII in the text and create a mapping of placeholders to original values
    '''
    if not text:
        return "", {}
    
    results = analyzer.analyze(text=text, entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"], language='en')
    pii_map = {}
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
    
    anonymized_text = anonymized_result.text
    
    # Map the Presidio placeholders to the original text
    for res in results:
        original_value = text[res.start:res.end]
        placeholder = f"<{res.entity_type}>" 
        pii_map[placeholder] = original_value

    return anonymized_text, pii_map

def deanonymize_text(text: str, pii_map: dict) -> str:
    '''
    Unmask PII in the text
    '''
    if not text or not pii_map:
        return text
    
    for placeholder, real_value in pii_map.items():
        text = text.replace(placeholder, real_value)
    return text