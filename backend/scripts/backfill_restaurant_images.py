from collections import defaultdict

from app.database import SessionLocal
from app.main import extract_business_image_url, search_pexels_fallback_images
from app.models import Restaurant, Session


def main() -> None:
    db = SessionLocal()
    scanned = 0
    updated_from_payload = 0
    updated_from_pexels = 0
    unchanged = 0
    missing_payload = 0
    still_missing = 0

    try:
        restaurants = db.query(Restaurant).all()
        missing_for_fallback: dict[tuple[str, str], list[Restaurant]] = defaultdict(list)

        for restaurant in restaurants:
            scanned += 1
            payload = restaurant.source_payload
            if not isinstance(payload, dict):
                missing_payload += 1
                session = db.get(Session, restaurant.session_id)
                cuisine = (session.cuisine if session and session.cuisine else restaurant.name).strip()
                location = (session.location_text if session and session.location_text else "").strip()
                missing_for_fallback[(cuisine, location)].append(restaurant)
                continue

            new_image_url = extract_business_image_url(payload)
            if new_image_url:
                if restaurant.image_url == new_image_url:
                    unchanged += 1
                    continue

                restaurant.image_url = new_image_url
                updated_from_payload += 1
                continue

            session = db.get(Session, restaurant.session_id)
            cuisine = (session.cuisine if session and session.cuisine else restaurant.name).strip()
            location = (session.location_text if session and session.location_text else "").strip()
            missing_for_fallback[(cuisine, location)].append(restaurant)

        for (cuisine, location), group in missing_for_fallback.items():
            query_parts = [cuisine or "restaurant", "restaurant food"]
            if location:
                query_parts.append(location)
            fallback_urls = search_pexels_fallback_images(" ".join(query_parts), len(group))

            for restaurant in group:
                if fallback_urls:
                    restaurant.image_url = fallback_urls.pop(0)
                    updated_from_pexels += 1
                else:
                    still_missing += 1

        db.commit()
    finally:
        db.close()

    print(f"scanned={scanned}")
    print(f"updated_from_payload={updated_from_payload}")
    print(f"updated_from_pexels={updated_from_pexels}")
    print(f"updated_total={updated_from_payload + updated_from_pexels}")
    print(f"unchanged={unchanged}")
    print(f"missing_payload={missing_payload}")
    print(f"still_missing={still_missing}")


if __name__ == "__main__":
    main()
