import re
import sys
from bs4 import BeautifulSoup
from services.privacy import mask_content

def preprocess(content, is_subject=True):
    """
    Strips HTML, normalizes, and masks PII
    """
    def extract_core_content(text):
        # Split on any forward/reply header pattern
        split_pattern = re.compile(
            r'(-{3,}\s*Forwarded message\s*-{3,}|On\s.+?wrote:)',
            re.DOTALL
        )
        
        parts = split_pattern.split(text)
        
        if len(parts) == 1:
            # Remove forwarding/reply chain
            return text.strip()
        
        # For forwards: take the LAST segment (deepest original message)
        # For replies: take the FIRST segment (the new content at the top)
        subject_lower = text.lower()
        is_forward = 'forwarded message' in subject_lower or text.lower().startswith('[subject] fwd')
        
        if is_forward:
            # Get the original email
            segments = [p.strip() for p in parts if p.strip() and not split_pattern.match(p.strip())]
            return segments[-1] if segments else text.strip()
        else:
            # Take everything before the first quoted section
            return parts[0].strip()

    def clean_text(text):
        '''
        Function that removes HTML tags, normalizes whitespace and strips quoted reply chains 
        '''
        # Remove HTML tags
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        
        # Normalize whitespacing
        text = ' '.join(text.split())

        # Strip quoted reply chains
        if not is_subject:
            text = extract_core_content(text)

        return text

    clean_content = clean_text(content)
    
    if not is_subject:
        clean_content = re.sub(r'^(From|To|Cc|Bcc|Date|Subject):.*?(Dear |Hi |Hello |To Whom)', 
                    r'\2', clean_content, flags=re.IGNORECASE)
        clean_content = ' '.join(clean_content.split())
    
    # Mask the content and create a map for unmasking
    masked_content, _ = mask_content(clean_content)
    
    return masked_content