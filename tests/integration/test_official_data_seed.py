"""Comprueba la carga repetible del catálogo en PostgreSQL desechable."""

import os

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.seed_catalogs import CatalogDocument, seed_catalog
from app.models import CurriculumContent, Grade, Subject


pytestmark = pytest.mark.skipif(
    os.getenv("COLEGIO_ALFA_TEST_AI_FLOW") != "1",
    reason="Requiere el entorno PostgreSQL aislado del runner integrado",
)


def test_catalog_seed_is_repeatable_and_preserves_existing_rows(flow_environment) -> None:
    document = CatalogDocument.model_validate(
        {
            "schema_version": 1,
            "source": {
                "name": "Catálogo ficticio de prueba",
                "version": "1",
                "reference": "Solo para una base desechable",
                "url": None,
                "approved_by": "Prueba automatizada",
                "approved_on": "2026-10-22",
            },
            "grades": [
                {
                    "name": "Quinto grado",
                    "subjects": [
                        {
                            "name": "Matemática",
                            "contents": [
                                "Fracciones equivalentes",
                                "Operaciones con fracciones",
                            ],
                        }
                    ],
                },
                {
                    "name": "Séptimo grado",
                    "subjects": [
                        {
                            "name": "Ciencias Naturales",
                            "contents": ["La célula"],
                        }
                    ],
                },
            ],
        }
    )

    with Session(flow_environment.engine) as session:
        original = session.get(CurriculumContent, flow_environment.content_id)
        assert original is not None
        original_values = (original.id, original.description)

        first = seed_catalog(session, document)
        counts_after_first = (
            session.scalar(select(func.count()).select_from(Grade)),
            session.scalar(select(func.count()).select_from(Subject)),
            session.scalar(select(func.count()).select_from(CurriculumContent)),
        )
        second = seed_catalog(session, document)
        counts_after_second = (
            session.scalar(select(func.count()).select_from(Grade)),
            session.scalar(select(func.count()).select_from(Subject)),
            session.scalar(select(func.count()).select_from(CurriculumContent)),
        )
        preserved = session.get(CurriculumContent, flow_environment.content_id)

    assert (first.created_grades, first.created_subjects, first.created_contents) == (
        1,
        1,
        2,
    )
    assert (second.created_grades, second.created_subjects, second.created_contents) == (
        0,
        0,
        0,
    )
    assert counts_after_second == counts_after_first
    assert preserved is not None
    assert (preserved.id, preserved.description) == original_values
