from typing import List

class NovaClassifier:
    def __init__(self):
        self.ultra_processed_markers = [
            "syrup", "artificial flavor", "colour", "color", "modified starch",
            "emulsifier", "preservative", "sweetener", "hydrolysed", "interesterified",
            "hydrogenated", "maltodextrin", "dextrose", "inverted sugar",
            "potassium sorbate", "sodium benzoate", "aspartame", "sucralose",
            "monosodium glutamate", "carrageenan"
        ]

    def classify(self, ingredients: List[str]) -> int:
        all_text = " ".join([i.lower() for i in ingredients])
        
        marker_count = 0
        for marker in self.ultra_processed_markers:
            if marker in all_text:
                marker_count += 1
        
        # Rule-based classification
        if marker_count >= 3 or len(ingredients) > 15:
            return 4  # Ultra-processed
        if marker_count >= 1 or len(ingredients) > 8:
            return 3  # Processed
        if len(ingredients) > 3 or "oil" in all_text or "sugar" in all_text:
            return 2  # Processed culinary ingredients
        return 1  # Unprocessed or minimally processed
