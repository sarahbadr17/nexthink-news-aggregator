from types import SimpleNamespace

from app.classification.categories import ArticleCategory
from app.classification import classifier


def test_classify_returns_valid_category(monkeypatch):
    fake_response = SimpleNamespace(output_text="Cybersecurity")

    def fake_create(*args, **kwargs):
        return fake_response

    monkeypatch.setattr(classifier.client.responses, "create", fake_create)

    category = classifier.classify(
        "Critical vulnerability found in firewall",
        "A major security issue affects enterprise devices."
    )

    assert category in list(ArticleCategory)
    assert category == ArticleCategory.CYBER