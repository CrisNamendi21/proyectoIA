import json

import pytest
from pydantic import ValidationError

from app.db.seed_catalogs import CatalogDocument, catalog_totals, load_catalog


def valid_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "source": {
            "name": "Documento curricular aprobado",
            "version": "2026",
            "reference": "Acta interna de aprobación",
            "url": "https://www.mined.gob.ni/",
            "approved_by": "Responsable autorizado del colegio",
            "approved_on": "2026-10-22",
        },
        "grades": [
            {
                "name": "Quinto grado",
                "subjects": [
                    {
                        "name": "Matemática",
                        "contents": ["Fracciones equivalentes"],
                    }
                ],
            }
        ],
    }


def test_load_catalog_validates_metadata_and_reports_fingerprint(tmp_path) -> None:
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(valid_payload()), encoding="utf-8")

    document, fingerprint = load_catalog(path)

    assert catalog_totals(document) == (1, 1, 1)
    assert len(fingerprint) == 64
    assert document.source.name == "Documento curricular aprobado"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.update(schema_version=2),
        lambda payload: payload["grades"].append(payload["grades"][0]),
        lambda payload: payload["grades"][0]["subjects"][0].update(contents=[" "]),
        lambda payload: payload["source"].update(approved_by=" "),
    ],
)
def test_catalog_rejects_unknown_version_duplicates_and_empty_text(mutation) -> None:
    payload = valid_payload()
    mutation(payload)

    with pytest.raises(ValidationError):
        CatalogDocument.model_validate(payload)
