import asyncio
import json
from pathlib import Path

from app.services.catalog import CatalogService


def test_load_catalog_and_find_node_and_normalize(tmp_path):
    root = {
        "id": "root",
        "title": "Root",
        "items": [
            {
                "id": "cat1",
                "type": "category",
                "title": "Cat 1",
                "items": [
                    {"id": "p1", "type": "product", "title": "Product 1"},
                    {"id": "p2", "type": "product", "title": "Product 2"},
                ],
            },
            {"id": "p3", "type": "product", "title": "Product 3"},
        ],
    }

    f = tmp_path / "catalog.json"
    f.write_text(json.dumps(root, ensure_ascii=False))

    svc = CatalogService(catalog_file=str(f))

    loaded = svc.load_catalog()
    assert isinstance(loaded, dict)
    assert loaded.get("id") == "root"

    node = asyncio.run(svc.find_node("p1"))
    assert node is not None and node.get("id") == "p1"

    svc._normalize_parents(loaded, None)
    found_cat = None
    for it in loaded.get("items", []):
        if it.get("id") == "cat1":
            found_cat = it
    assert found_cat is not None
    assert any((it.get("parent_id") == "cat1") for it in found_cat.get("items", []))


def test_load_from_file_async(tmp_path):
    content = {"id": "root", "items": []}
    f = tmp_path / "catalog2.json"
    f.write_text(json.dumps(content))

    svc = CatalogService(catalog_file=str(f))
    loaded = asyncio.run(svc.load_from_file(str(f)))
    assert loaded.get("id") == "root"


def test_project_data_files_exist():
    base = Path(__file__).resolve().parents[1]
    data_dir = base / "data"
    assert (data_dir / "catalog.json").exists()
    assert (data_dir / "ranks.json").exists()
