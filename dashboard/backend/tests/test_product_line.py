"""Universal service model — product_line truth."""

from app.integration.product_line import (
    LIFECYCLE_DIALOG,
    ONE_TIME_SERVICES,
    SERVICE_WEBSITE,
    SUBSCRIPTION_TIERS,
    artifact_label_ru,
    service_label_ru,
    universal_approved_purchase_options,
    universal_concept_ready_message,
    universal_service_intro,
    universal_service_model_rules,
    website_studio_intro,
)


def test_lifecycle_stages_defined():
    assert LIFECYCLE_DIALOG == "dialog"
    assert len(ONE_TIME_SERVICES) >= 10


def test_website_alias_matches_universal():
    assert website_studio_intro() == universal_service_intro(SERVICE_WEBSITE)


def test_universal_intro_mentions_multimodal():
    text = universal_service_intro(SERVICE_WEBSITE)
    assert "голосом" in text
    assert "один проект" in text


def test_concept_ready_not_final_sale():
    text = universal_concept_ready_message(SERVICE_WEBSITE)
    assert "первая версия" in text.lower()
    assert "проект" in text.lower()


def test_approved_options_two_paths():
    text = universal_approved_purchase_options(SERVICE_WEBSITE)
    assert "Ваш проект сохранён" in text
    assert "разовая покупка" in text.lower()
    assert "подписка" in text.lower()
    assert "ничего не навязываю" in text


def test_subscription_tiers_customer_names():
    names = [t["customer_name_ru"] for t in SUBSCRIPTION_TIERS]
    assert names == ["Free", "Professional", "Business", "Enterprise"]


def test_service_labels():
    assert service_label_ru(SERVICE_WEBSITE) == "Сайт для бизнеса"
    assert artifact_label_ru(SERVICE_WEBSITE) == "Website"


def test_model_rules_cover_all_services():
    rules = universal_service_model_rules()
    for svc in ONE_TIME_SERVICES:
        assert svc["customer_name_ru"] in rules
    for tier in SUBSCRIPTION_TIERS:
        assert tier["customer_name_ru"] in rules
    assert "Internal CEO Edition" in rules
    assert "Product Principles" in rules
    assert "Professional" in rules
