"""Budget ↔ institution links (A-014), budget entities in search, and history."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.budget.history import record_snapshots
from app.budget.links import index_budget_entities, link_budget_institutions
from app.budget.models import BudgetSnapshot
from app.core.relationships import Relationship
from app.ingestion.datasets import budget, entities
from app.ingestion.pipeline import run_sync
from app.sources.registry import seed_registry
from tests.samples import budget_row, entity_row

API = "/api/v1"


@pytest.fixture
def loaded(session: Session) -> None:
    seed_registry(session)
    run_sync(
        session,
        entities.SPEC,
        [
            # Same name without accents or capitals: linked.
            entity_row("9001", nombre="Agencia de Ejemplo"),
            # Two directory entries with one name: ambiguous, never linked.
            entity_row("9002", nombre="SUPERINTENDENCIA DE EJEMPLO"),
            entity_row("9003", nombre="Superintendencia de Ejemplo"),
            # Only a prefix of the budget name: not linked (no loose matching).
            entity_row("9004", nombre="MINISTERIO DE EJEMPLO"),
        ],
    )
    run_sync(
        session,
        budget.SPEC,
        [
            budget_row(nombre_entidad="AGENCIA DE EJEMPLO"),
            budget_row(nombre_entidad="AGENCIA DE EJEMPLO", recurso_presupuestal="DONACIONES"),
            budget_row("98-01-00", nombre_entidad="SUPERINTENDENCIA DE EJEMPLO"),
            budget_row("97-01-00", nombre_entidad="MINISTERIO DE EJEMPLO - GESTIÓN GENERAL"),
        ],
    )


def test_only_exact_unique_names_are_linked(session: Session, loaded: None) -> None:
    result = link_budget_institutions(session)
    assert (result.budget_entities, result.linked) == (3, 1)
    links = list(session.scalars(select(Relationship)))
    # One link per budget line of the linked entity, all labelled as analysis.
    assert len(links) == 2
    assert {link.epistemic_label for link in links} == {"hipotesis_analitica"}
    assert {link.confidence_class for link in links} == {"analytical_association"}
    assert all(link.source_record_id and "A-014" in (link.method_note or "") for link in links)


def test_relinking_replaces_previous_links(session: Session, loaded: None) -> None:
    link_budget_institutions(session)
    link_budget_institutions(session)
    assert session.scalar(select(func.count()).select_from(Relationship)) == 2


def test_links_show_both_ways(client: TestClient, session: Session, loaded: None) -> None:
    link_budget_institutions(session)
    entity = client.get(f"{API}/budget/entities/99-01-00").json()
    assert entity["linked_institution"]["name"] == "Agencia de Ejemplo"
    assert "no un dato oficial" in entity["linked_institution_rule"]
    institution = client.get(
        f"{API}/institutions/{entity['linked_institution']['institution_id']}"
    ).json()
    assert institution["budget_entity"] == {
        "entity_code": "99-01-00",
        "entity_name": "AGENCIA DE EJEMPLO",
    }
    unlinked = client.get(f"{API}/budget/entities/97-01-00").json()
    assert unlinked["linked_institution"] is None


def test_budget_entities_are_searchable_by_code(
    client: TestClient, session: Session, loaded: None
) -> None:
    assert index_budget_entities(session) == 3
    session.commit()
    body = client.get(f"{API}/search", params={"q": "agencia ejemplo", "type": "budget_entity"})
    hits = body.json()["items"]
    assert [(hit["title"], hit["record_key"]) for hit in hits] == [
        ("AGENCIA DE EJEMPLO", "99-01-00")
    ]
    by_code = client.get(f"{API}/search", params={"q": "98-01-00"}).json()["items"]
    assert by_code[0]["record_key"] == "98-01-00"


def test_history_keeps_one_row_per_update_date(
    client: TestClient, session: Session, loaded: None
) -> None:
    assert record_snapshots(session) == 3
    assert record_snapshots(session) == 3  # same update date: overwritten, not duplicated
    session.commit()
    # The source publishes an update: new figures under a new date.
    run_sync(
        session,
        budget.SPEC,
        [
            budget_row(
                nombre_entidad="AGENCIA DE EJEMPLO",
                compromisos="900000",
                obligaciones="600000",
                pagos="500000",
                **{":updated_at": "2026-12-05T10:00:00.000Z"},
            )
        ],
    )
    record_snapshots(session)
    session.commit()
    assert session.scalar(select(func.count()).select_from(BudgetSnapshot)) == 4
    history = client.get(f"{API}/budget/entities/99-01-00").json()["history"]
    assert [row["published_on"] for row in history] == ["2026-11-07", "2026-12-05"]
    assert Decimal(history[0]["amounts"]["commitments"]) == Decimal(800000) * 2
    assert Decimal(history[1]["amounts"]["commitments"]) == Decimal(900000) + 800000
