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

    def get_popular_dishes(self, business_id: str) -> list[dict]:
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host,
        }
        url = f"{self.base_url}/popular_dish"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers, params={"business_id": business_id})
            if response.status_code >= 400:
                return []
        except httpx.HTTPError:
            return []
        payload = response.json()
        return payload.get("data", {}).get("popular_dishes", [])

    def get_reviews(self, business_id: str, count: int = 3) -> list[dict]:
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host,
        }
        url = f"{self.base_url}/reviews"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    url,
                    headers=headers,
                    params={"business_id": business_id, "reviews_per_page": count, "sort_by": "Yelp_sort"},
                )
            if response.status_code >= 400:
                return []
        except httpx.HTTPError:
            return []
        raw = response.json().get("reviews", [])
        results = []
        for r in raw:
            profile_photo = (r.get("author") or {}).get("profilePhoto") or {}
            photo_url = (profile_photo.get("photoUrl") or {}).get("userSrc")
            results.append({
                "text": (r.get("text") or {}).get("full", ""),
                "rating": r.get("rating", 0),
                "author_name": (r.get("author") or {}).get("displayName", ""),
                "author_location": (r.get("author") or {}).get("displayLocation"),
                "author_photo_url": photo_url,
                "created_at": r.get("reviewCreatedAt", ""),
            })
        return results
