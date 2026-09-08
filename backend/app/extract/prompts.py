EXTRACT_PROMPT = """You extract grounded facts from one PDF page.
Return JSON: {{"facts": [{{"statement": str, "subject": str, "predicate": str,
"object_raw": str, "value_num": number|null, "unit": str|null, "period": str|null,
"scope": str|null, "quote": str, "confidence": number, "extra": object}}]}}
Rules:
- quote MUST be a verbatim substring of PAGE TEXT.
- Only real claims (metrics, dates, entity roles, definitions). Skip TOC/headers.
- extra holds attributes that do not fit the core fields.
PAGE TEXT:
"""
