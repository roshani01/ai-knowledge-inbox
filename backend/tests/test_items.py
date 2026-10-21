import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_items_empty_inbox(client: AsyncClient):
    response = await client.get("/items")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_items_ordering_and_structure(client: AsyncClient, mock_openai_embedder):
    # Ingest two items
    await client.post(
        "/ingest",
        json={"source_type": "note", "title": "Item Alpha", "content": "Alpha content details"},
    )
    await client.post(
        "/ingest",
        json={"source_type": "note", "title": "Item Beta", "content": "Beta content details"},
    )

    response = await client.get("/items")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    # Check newest first: Item Beta should come before Item Alpha
    titles = [item["title"] for item in data["items"]]
    assert "Item Beta" in titles
    assert "Item Alpha" in titles
    assert titles.index("Item Beta") < titles.index("Item Alpha")

    # Verify item response fields
    first = data["items"][0]
    assert "id" in first
    assert "title" in first
    assert "source_type" in first
    assert "indexing_status" in first
    assert "preview" in first
    assert "chunk_count" in first
    assert "created_at" in first


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient, mock_openai_embedder):
    # Ingest an item
    create_res = await client.post(
        "/ingest",
        json={"source_type": "note", "title": "Item To Delete", "content": "Will be deleted"},
    )
    assert create_res.status_code in (200, 201)
    item_id = create_res.json()["id"]

    # Delete it
    del_res = await client.delete(f"/items/{item_id}")
    assert del_res.status_code == 200

    # Ensure it's not in items list
    list_res = await client.get("/items")
    ids = [it["id"] for it in list_res.json()["items"]]
    assert item_id not in ids

    # Deleting again should return 404
    del_404 = await client.delete(f"/items/{item_id}")
    assert del_404.status_code == 404

