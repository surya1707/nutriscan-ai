from app.services.nova_classifier import NovaClassifier

def test_nova_classify():
    classifier = NovaClassifier()
    
    # Unprocessed
    assert classifier.classify(["apple"]) == 1
    
    # Processed culinary ingredients
    assert classifier.classify(["apple", "sugar"]) == 2
    
    # Processed (1 marker)
    assert classifier.classify(["apple", "sugar", "artificial flavor"]) == 3
    
    # Ultra-processed (>= 3 markers)
    assert classifier.classify(["water", "syrup", "artificial flavor", "color"]) == 4
    
    # Ultra-processed (length > 15)
    long_ingredients = [f"ingredient_{i}" for i in range(20)]
    assert classifier.classify(long_ingredients) == 4
