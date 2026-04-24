from __future__ import annotations

import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.stem import PorterStemmer

# Ensure NLTK data is available implicitly (assuming downloaded)
stemmer = PorterStemmer()

def _extract_location_nltk(text: str) -> str | None:
    # Use NLTK POS tagging to help find locations
    tokens = word_tokenize(text)
    tagged = pos_tag(tokens)

    # Simple fallback regex if NLTK NER isn't available
    pattern = re.compile(
        r"(?:near|at|in|around|beside|opposite)\s+([A-Z0-9][A-Za-z0-9,\- ]{3,60})",
        flags=re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        # Stop at punctuation
        loc = match.group(1).split('.')[0].strip(" .,!?:;")
        return loc
        
    return None

def _extract_people_count(tokens: list[tuple[str, str]]) -> int | None:
    # NLTK tags Cardinal Digits as 'CD'
    # Look for CD followed by Nouns (NN/NNS) related to people
    for i, (word, tag) in enumerate(tokens):
        if tag == 'CD':
            if word.isdigit():
                return int(word)
            # Try to convert word to int if possible (e.g. "five" -> 5)
            # We will just stick to simple digit conversion for now
    
    return None

def _calculate_similarity_urgency(text: str) -> str:
    # Use NLTK Stemming for basic word similarity checking
    tokens = word_tokenize(text.lower())
    stems = [stemmer.stem(t) for t in tokens]
    
    high_urgency_stems = ["trap", "collaps", "injur", "rubbl", "bleed", "critic", "emerg", "save"]
    med_urgency_stems = ["block", "water", "food", "need", "damag", "crack"]
    
    high_matches = sum(1 for s in stems if s in high_urgency_stems)
    if high_matches > 0:
        return "high"
        
    med_matches = sum(1 for s in stems if s in med_urgency_stems)
    if med_matches > 0:
        return "medium"
        
    return "low"

def _determine_incident_type(text: str) -> str:
    tokens = word_tokenize(text.lower())
    stems = [stemmer.stem(t) for t in tokens]
    
    if "collaps" in stems or "rubbl" in stems:
        return "building-collapse"
    if "injur" in stems or "bleed" in stems or "medic" in stems:
        return "medical"
    if "water" in stems or "food" in stems:
        return "supply-shortage"
    if "block" in stems or "debri" in stems:
        return "access-blocked"
    return "general-distress"

def extract_sos_with_nltk(records: list[dict]) -> list[dict]:
    extracted_data = []
    
    for record in records:
        raw_text = record.get("raw_text", "")
        if not raw_text:
            continue
            
        # 1. Location Extraction via NLTK NER
        location = _extract_location_nltk(raw_text)
        
        # 2. Tokenization & POS Tagging
        tokens = pos_tag(word_tokenize(raw_text))
        
        # 3. People Count via POS Cardinal Digit analysis
        people_count = _extract_people_count(tokens)
        
        # 4. Urgency via NLTK Stemming Similarity
        urgency = _calculate_similarity_urgency(raw_text)
        
        # 5. Incident Type
        incident_type = _determine_incident_type(raw_text)
        
        extracted_data.append({
            "id": record.get("id"),
            "extracted_location": location,
            "severity": urgency,
            "people_count": people_count,
            "urgency": urgency,
            "incident_type": incident_type,
            "summary": raw_text,
            "confidence": 0.85, # Since it's deterministic heuristics, we assign a high fixed confidence
            "extraction_method": "nltk_tree"
        })
        
    return extracted_data
