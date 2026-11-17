from app.core.labels import ConfidenceClass, EpistemicLabel


def test_epistemic_labels_match_the_brief() -> None:
    assert {label.value for label in EpistemicLabel} == {
        "hecho_documentado",
        "interpretacion_juridica",
        "hipotesis_analitica",
        "simulacion_hipotetica",
        "no_verificado",
    }


def test_confidence_classes_match_the_brief() -> None:
    assert {c.value for c in ConfidenceClass} == {
        "verified_official",
        "declared",
        "reported",
        "historical",
        "analytical_association",
        "unverified_claim",
    }
