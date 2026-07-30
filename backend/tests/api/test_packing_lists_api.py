"""API tests for packing lists."""

from httpx import ASGITransport, AsyncClient


async def test_packing_list_crud_flow(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = (
            await client.post(
                "/api/packing-lists",
                json={"title": "Camping trip", "notes": "Summer"},
            )
        ).json()
        list_id = created["id"]

        item = (
            await client.post(
                f"/api/packing-lists/{list_id}/entries",
                json={"entry_type": "item", "title": "Tent"},
            )
        ).json()
        question = (
            await client.post(
                f"/api/packing-lists/{list_id}/entries",
                json={
                    "entry_type": "question",
                    "title": "Do I need formal clothes?",
                },
            )
        ).json()

        await client.patch(
            f"/api/packing-lists/entries/{item['id']}",
            json={"is_checked": True},
        )
        await client.patch(
            f"/api/packing-lists/entries/{question['id']}",
            json={"answer": "no"},
        )

        detail = (await client.get(f"/api/packing-lists/{list_id}")).json()
        summaries = (await client.get("/api/packing-lists")).json()

        await client.delete(f"/api/packing-lists/{list_id}")

    assert detail["title"] == "Camping trip"
    assert len(detail["entries"]) == 2
    assert summaries[0]["item_count"] == 1
    assert summaries[0]["question_count"] == 1
