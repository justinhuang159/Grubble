import httpx


class YelpClientError(Exception):
    pass


class MissingRapidAPIConfigError(YelpClientError):
    pass


class YelpClient:
    def __init__(self, api_key: str, api_host: str, base_url: str) -> None:
        self.api_key = api_key
        self.api_host = api_host
        self.base_url = base_url.rstrip("/")

    def search_businesses(
        self,
        *,
        term: str,
        location: str,
        price: str | None,
        radius_meters: int | None,
        limit: int = 30,
    ) -> list[dict]:
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host,
        }
        params: dict[str, str | int] = {
            "search_term": term,
            "location": location,
            "limit": limit,
            "offset": 0,
            "business_details_type": "basic",
        }
        if price:
            params["price"] = price
        if radius_meters:
            params["radius"] = radius_meters

        url = f"{self.base_url}/search"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers, params=params)
            if response.status_code >= 400:
                detail = response.text[:300]
                raise YelpClientError(
                    f"RapidAPI Yelp returned {response.status_code}: {detail}"
                )
        except httpx.HTTPError as exc:
            raise YelpClientError("Failed to fetch restaurants from RapidAPI Yelp") from exc

        payload = response.json()

        # RapidAPI Yelp providers vary in response envelope.
        businesses = None
        if isinstance(payload, dict):
            if isinstance(payload.get("businesses"), list):
                businesses = payload["businesses"]
            elif isinstance(payload.get("results"), list):
                businesses = payload["results"]
            elif isinstance(payload.get("data"), list):
                businesses = payload["data"]
            elif isinstance(payload.get("business_search_result"), list):
                businesses = payload["business_search_result"]
            elif isinstance(payload.get("ad_business_search_result"), list):
                businesses = payload["ad_business_search_result"]
        elif isinstance(payload, list):
            businesses = payload

        if not isinstance(businesses, list):
            if isinstance(payload, dict):
                keys = ", ".join(sorted(payload.keys()))
                raise YelpClientError(
                    f"RapidAPI Yelp response missing list field. Top-level keys: [{keys}]"
                )
            raise YelpClientError("RapidAPI Yelp response missing list field")

        return businesses
