"""Unit tests for automatic code classifier."""

from classifier import CodeClassifier, CATEGORIES


def test_classifier_initialization_and_metadata():
    classifier = CodeClassifier()
    assert classifier.is_trained is True

    info = classifier.get_dataset_info()
    assert info["total_samples"] >= 30
    for cat in CATEGORIES:
        assert cat in info["category_distribution"]
        assert info["category_distribution"][cat] > 0
    assert "disclaimer" in info


def test_classifier_predict_categories():
    classifier = CodeClassifier()

    # 1. Authentication
    res_auth = classifier.predict(
        "def login_user(username, password):\n    token = jwt.encode({'user': username}, SECRET)"
    )
    assert res_auth.category == "Authentication"
    assert 0.0 <= res_auth.confidence <= 1.0
    assert len(res_auth.probabilities) == 6

    # 2. Database Operations
    res_db = classifier.predict(
        "def query_users(cursor):\n    cursor.execute('SELECT * FROM users WHERE status = ?', ('active',))\n    return cursor.fetchall()"
    )
    assert res_db.category == "Database Operations"

    # 3. Testing
    res_test = classifier.predict(
        "def test_order_submission_status(mock_client):\n    res = mock_client.post('/orders')\n    assert res.status_code == 201"
    )
    assert res_test.category == "Testing"

    # 4. Business Logic
    res_biz = classifier.predict(
        "def calculate_tiered_discount(subtotal: float, tier: str) -> float:\n    if tier == 'VIP': return subtotal * 0.8"
    )
    assert res_biz.category == "Business Logic"


def test_classifier_empty_input_fallback():
    classifier = CodeClassifier()
    res = classifier.predict("")
    assert res.category in CATEGORIES
    assert res.confidence > 0.0
