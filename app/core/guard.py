import re

# 1. SOS Keywords (Multilingual for the West Bengal context)
SOS_KEYWORDS = [
    "sos", "help", "danger", "emergency", "police", 
    "bachao", "rakkha korun", "aapatkal", "musibat"
]

def is_emergency(text: str) -> bool:
    """
    Rapidly scans incoming text for immediate danger signals.
    Returns True if an emergency is detected, bypassing standard routing.
    """
    if not text:
        return False

    cleaned_text = text.lower().strip()
    
    # 2. Direct Keyword Match
    # Checks if any SOS words appear in the user's message
    if any(word in cleaned_text for word in SOS_KEYWORDS):
        return True
    
    # 3. Stress Pattern Match (The "Shouting" Rule)
    # Detects messages in ALL CAPS that also contain exclamation marks
    # Example: "I AM IN DANGER!" or "HELP!!"
    if text.isupper() and "!" in text:
        return True
    
    # 4. Regex for repeated punctuation
    # Multiple exclamation marks often indicate panic
    if re.search(r'!!+', text):
        return True
        
    return False

# Quick test logic
if __name__ == "__main__":
    test_msg = "HELP!! I am near the market"
    if is_emergency(test_msg):
        print("🚨 Emergency Detected: Routing to Durga Node.")
    else:
        print("✅ Standard Query: Routing to Supervisor.")