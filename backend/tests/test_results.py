import pytest


def create_active_session(client, monkeypatch: pytest.MonkeyPatch, participants: list[str] | None = None) -> str:
    participants = participants or []
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    monkeypatch.setenv("RAPIDAPI_HOST", "example-host")
    monkeypatch.delenv("USE_MOCK_YELP", raising=False)

    from app import main as main_module

    def fake_search(
        self, *, term: str, location: str, price: str | None, radius_meters: int | None, limit: int = 30
    ):
        return [
            {"id": "rest-a", "name": "A Place", "location": {"display_address": ["1 Main St"]}},
            {"id": "rest-b", "name": "B Place", "location": {"display_address": ["2 Main St"]}},
            {"id": "rest-c", "name": "C Place", "location": {"display_address": ["3 Main St"]}},
        ]

    monkeypatch.setattr(main_module.YelpClient, "search_businesses", fake_search)

    create_res = client.post(
        "/sessions",
        json={
            "host_name": "Justin",
            "cuisine": "sushi",
            "price": "1,2",
            "radius_meters": 3000,
            "location_text": "San Francisco, CA",
        },
    )
    assert create_res.status_code == 200
    room_code = create_res.json()["room_code"]

    for user_name in participants:
        join_res = client.post(f"/sessions/{room_code}/join", json={"user_name": user_name})
        assert join_res.status_code == 200

    start_res = client.post(f"/sessions/{room_code}/start", json={"host_name": "Justin"})
    assert start_res.status_code == 200
    return room_code


def test_results_ranked_by_yes_votes_desc(monkeypatch: pytest.MonkeyPatch, client) -> None:
    room_code = create_active_session(client, monkeypatch, participants=["Alex", "Sam"])

    first_restaurant_id = client.get(
        f"/sessions/{room_code}/restaurants/next", params={"user_name": "Justin"}
    ).json()["restaurant"]["id"]

    # Restaurant A: 2 yes, 1 no
    host_vote_a = client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Justin", "restaurant_id": first_restaurant_id, "decision": "yes"},
    )
    assert host_vote_a.status_code == 200
    second_restaurant_id = host_vote_a.json()["next_restaurant"]["id"]
    assert client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Alex", "restaurant_id": first_restaurant_id, "decision": "yes"},
    ).status_code == 200
    assert client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Sam", "restaurant_id": first_restaurant_id, "decision": "no"},
    ).status_code == 200

    # Restaurant B: 1 yes, 2 no
    assert client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Justin", "restaurant_id": second_restaurant_id, "decision": "no"},
    ).status_code == 200
    assert client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Alex", "restaurant_id": second_restaurant_id, "decision": "yes"},
    ).status_code == 200
    assert client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Sam", "restaurant_id": second_restaurant_id, "decision": "no"},
    ).status_code == 200

    res = client.get(f"/sessions/{room_code}/results")
    assert res.status_code == 200
    payload = res.json()
    assert payload["total_participants"] == 3
    assert payload["results"][0]["restaurant"]["id"] == first_restaurant_id
    assert payload["results"][0]["yes_votes"] == 2
    assert payload["results"][1]["restaurant"]["id"] == second_restaurant_id
    assert payload["results"][1]["yes_votes"] == 1


def test_results_tie_breaker_uses_total_votes_desc(monkeypatch: pytest.MonkeyPatch, client) -> None:
    room_code = create_active_session(client, monkeypatch, participants=["Alex"])

    first_restaurant_id = client.get(
        f"/sessions/{room_code}/restaurants/next", params={"user_name": "Justin"}
    ).json()["restaurant"]["id"]

    # Restaurant A: 1 yes, 2 total votes
    host_vote_a = client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Justin", "restaurant_id": first_restaurant_id, "decision": "yes"},
    )
    assert host_vote_a.status_code == 200
    second_restaurant_id = host_vote_a.json()["next_restaurant"]["id"]
    assert client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Alex", "restaurant_id": first_restaurant_id, "decision": "no"},
    ).status_code == 200

    # Restaurant B: 1 yes, 1 total vote
    assert client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Justin", "restaurant_id": second_restaurant_id, "decision": "yes"},
    ).status_code == 200

    res = client.get(f"/sessions/{room_code}/results")
    assert res.status_code == 200
    payload = res.json()
    assert payload["results"][0]["restaurant"]["id"] == first_restaurant_id
    assert payload["results"][0]["yes_votes"] == 1
    assert payload["results"][0]["total_votes"] == 2
    assert payload["results"][1]["restaurant"]["id"] == second_restaurant_id
    assert payload["results"][1]["yes_votes"] == 1
    assert payload["results"][1]["total_votes"] == 1
