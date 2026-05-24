from backend.strategy.utils.scorer import CompositeScorer, RiskClassifier


def test_composite_scorer():
    scorer = CompositeScorer()
    score = scorer.compute(
        predicted_return=10,
        momentum_score=70,
        quality_score=80,
        sentiment_score=60,
    )
    assert 0 <= score <= 100


def test_risk_classifier_low():
    rc = RiskClassifier(low_threshold=30, medium_threshold=60)
    assert rc.classify(20) == "low"


def test_risk_classifier_medium():
    rc = RiskClassifier(low_threshold=30, medium_threshold=60)
    assert rc.classify(45) == "medium"


def test_risk_classifier_high():
    rc = RiskClassifier(low_threshold=30, medium_threshold=60)
    assert rc.classify(75) == "high"
