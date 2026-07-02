from gither.value import value_model


def test_value_model_rejects_commit_farming() -> None:
    model = value_model()

    assert "Code earns only when it is actually used." in model
    assert "commit farming" in model
    assert "Pulse records real usage" in model
    assert "Knitweb records dependency relationships" in model
    assert "peer-to-peer duplicate of GitHub" in model
    assert "GitLab can also be a mirror" in model
    assert "The enrichment score is not a royalty split." in model
