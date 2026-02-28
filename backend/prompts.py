LLAMA_CLASSIFICATION_PROMPT = """
You are a precise email classifier. Analyze the email below and return EXACTLY a valid JSON object with 'category' and 'urgency'. Do not output any markdown or conversational text.

CATEGORIES:
- Work: Direct messages from colleagues, clients, or specific project updates.
- Transactional: Receipts, shipping updates, password resets, subscriptions.
- Newsletter: Automated job alerts, promotional offers, marketing, and mailing lists.
- Personal: Messages from real human friends or family.

URGENCY SCALE:
1 - Very Low: Promotions, marketing, spam, glasses sales.
2 - Low: Automated digests, receipts, subscription notices, LinkedIn job alerts.
3 - Normal: Standard emails requiring an eventual response.
4 - High: Time-sensitive tasks, meetings happening today.
5 - Critical: Server outages, absolute emergencies.

Example 1:
Email: "LinkedIn: 10 new Machine Learning Engineer roles in your area. Apply to IBM and more..."
Output: {{"category": "Newsletter", "urgency": 2}}

Example 2:
Email: "Massive Weekend Sale! Get 50% off all prescription glasses."
Output: {{"category": "Newsletter", "urgency": 1}}

Example 3:
Email: "Your Cosmo: Learn GenAI subscription from CodeSignal on Google Play will be canceled on Oct 14."
Output: {{"category": "Transactional", "urgency": 2}}

Example 4:
Email: "Hey man, are we still on for grabbing food on Friday?"
Output: {{"category": "Personal", "urgency": 3}}

Example 5:
Email: "Production server is down! We need a fix immediately."
Output: {{"category": "Work", "urgency": 5}}

Now analyze this email:
Email: {email_text}
Output:
"""

GEMINI_SUMMARIZATION_PROMPT = """
Analyze these {num_emails} emails. 
CRITICAL: If an email contains harmful or dangerous content, summarize it as "Content blocked due to safety concerns."

EMAILS:
{email_blocks}

Return exactly this JSON list structure:
[
    {{
        "id": <id>,
        "summary": "25-word action-oriented summary."
    }}
]
"""