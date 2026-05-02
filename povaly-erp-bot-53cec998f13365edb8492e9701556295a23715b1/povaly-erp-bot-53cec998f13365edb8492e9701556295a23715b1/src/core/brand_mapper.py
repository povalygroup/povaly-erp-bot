"""Brand name to code mapper."""

from typing import Optional, Dict


class BrandMapper:
    """Maps full brand names to short codes."""
    
    # Default brand mappings
    DEFAULT_MAPPINGS = {
        # Full brand name (case-insensitive) -> Short code (3 chars)
        # VorosaBajar variations (note: "bajar" vs "bazar")
        "vorosabazar": "VRB",
        "vorosabazaar": "VRB",
        "vorosabajar": "VRB",  # Common spelling
        "vorosa bajar": "VRB",
        "vorosabajaar": "VRB",
        "vorosabajor": "VRB",
        "vrb": "VRB",  # Direct code
        # GSMAura variations
        "gsmaura": "GSM",
        "gsm aura": "GSM",
        "gsm": "GSM",  # Direct code
        # Povaly variations
        "povaly": "POV",
        "pov": "POV",  # Direct code
    }
    
    # Display names for each brand code (for showing in /brand command)
    BRAND_DISPLAY_NAMES = {
        "VRB": "VorosaBajar",
        "GSM": "GSMAura",
        "POV": "Povaly",
    }
    
    def __init__(self, custom_mappings: Optional[Dict[str, str]] = None):
        """
        Initialize brand mapper.
        
        Args:
            custom_mappings: Optional custom brand mappings to add/override
        """
        self.mappings = self.DEFAULT_MAPPINGS.copy()
        if custom_mappings:
            # Convert keys to lowercase for case-insensitive matching
            self.mappings.update({k.lower(): v for k, v in custom_mappings.items()})
    
    def get_code(self, brand_name: str) -> Optional[str]:
        """
        Get brand code from full brand name.
        
        Args:
            brand_name: Full brand name (e.g., "VorosaBajar", "GSMAura", "Povaly")
        
        Returns:
            Brand code (e.g., "VRB", "GSM", "POV") or None if not found
        """
        # Remove # symbol if present
        brand_name = brand_name.replace('#', '').strip()
        brand_lower = brand_name.lower()
        
        # Try exact match (case-insensitive)
        code = self.mappings.get(brand_lower)
        if code:
            return code
        
        # Try partial match - find the longest matching known brand
        best_match = None
        best_match_len = 0
        
        for known_brand, code in self.mappings.items():
            # Check if known brand is contained in input (case-insensitive)
            if known_brand in brand_lower:
                if len(known_brand) > best_match_len:
                    best_match = code
                    best_match_len = len(known_brand)
        
        if best_match:
            return best_match
        
        # Try reverse - check if input is contained in any known brand
        for known_brand, code in self.mappings.items():
            if brand_lower in known_brand:
                if len(brand_lower) > best_match_len:
                    best_match = code
                    best_match_len = len(brand_lower)
        
        if best_match:
            return best_match
        
        # No match found
        return None
    
    def add_mapping(self, brand_name: str, code: str):
        """
        Add a new brand mapping.
        
        Args:
            brand_name: Full brand name
            code: Short brand code
        """
        self.mappings[brand_name.lower()] = code.upper()
    
    def get_all_codes(self) -> list:
        """Get all registered brand codes."""
        return list(set(self.mappings.values()))
    
    def get_display_name(self, code: str) -> str:
        """
        Get display name for a brand code.
        
        Args:
            code: Brand code (e.g., "VB", "GSM")
        
        Returns:
            Display name (e.g., "VorosaBajar", "GSMAura")
        """
        return self.BRAND_DISPLAY_NAMES.get(code.upper(), code)
