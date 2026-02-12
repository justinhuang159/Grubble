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


def test_get_next_restaurant_returns_first_unvoted(monkeypatch: pytest.MonkeyPatch, client) -> None:
    room_code = create_active_session(client, monkeypatch)
    res = client.get(f"/sessions/{room_code}/restaurants/next", params={"user_name": "Justin"})
    assert res.status_code == 200
    payload = res.json()
    assert payload["restaurant"] is not None
    assert payload["restaurant"]["name"] == "A Place"


def test_submit_vote_returns_next_and_progress(monkeypatch: pytest.MonkeyPatch, client) -> None:
    room_code = create_active_session(client, monkeypatch, participants=["Alex"])
    next_res = client.get(f"/sessions/{room_code}/restaurants/next", params={"user_name": "Justin"})
    restaurant_id = next_res.json()["restaurant"]["id"]

    vote_res = client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Justin", "restaurant_id": restaurant_id, "decision": "yes"},
    )
    assert vote_res.status_code == 200
    payload = vote_res.json()
    assert payload["duplicate"] is False
    assert payload["matched"] is False
    assert payload["total_participants"] == 2
    assert payload["yes_votes_for_restaurant"] == 1
    assert payload["next_restaurant"] is not None
    assert payload["next_restaurant"]["name"] == "B Place"


def test_submit_vote_is_idempotent_for_same_decision(monkeypatch: pytest.MonkeyPatch, client) -> None:
    room_code = create_active_session(client, monkeypatch)
    next_res = client.get(f"/sessions/{room_code}/restaurants/next", params={"user_name": "Justin"})
    restaurant_id = next_res.json()["restaurant"]["id"]

    first_vote = client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Justin", "restaurant_id": restaurant_id, "decision": "no"},
    )
    assert first_vote.status_code == 200

    second_vote = client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Justin", "restaurant_id": restaurant_id, "decision": "no"},
    )
    assert second_vote.status_code == 200
    assert second_vote.json()["duplicate"] is True


def test_submit_vote_conflicting_duplicate_rejected(monkeypatch: pytest.MonkeyPatch, client) -> None:
    room_code = create_active_session(client, monkeypatch)
    next_res = client.get(f"/sessions/{room_code}/restaurants/next", params={"user_name": "Justin"})
    restaurant_id = next_res.json()["restaurant"]["id"]

    first_vote = client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Justin", "restaurant_id": restaurant_id, "decision": "no"},
    )
    assert first_vote.status_code == 200

    second_vote = client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Justin", "restaurant_id": restaurant_id, "decision": "yes"},
    )
    assert second_vote.status_code == 409


def test_match_detected_when_all_participants_vote_yes(monkeypatch: pytest.MonkeyPatch, client) -> None:
    room_code = create_active_session(client, monkeypatch, participants=["Alex"])
    first_restaurant = client.get(
        f"/sessions/{room_code}/restaurants/next", params={"user_name": "Justin"}
    ).json()["restaurant"]["id"]

    host_vote = client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Justin", "restaurant_id": first_restaurant, "decision": "yes"},
    )
    assert host_vote.status_code == 200
    assert host_vote.json()["matched"] is False

    second_vote = client.post(
        f"/sessions/{room_code}/votes",
        json={"user_name": "Alex", "restaurant_id": first_restaurant, "decision": "yes"},
    )
    assert second_vote.status_code == 200
    payload = second_vote.json()
    assert payload["matched"] is True
    assert payload["matched_restaurant_id"] == first_restaurant
