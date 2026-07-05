from __future__ import annotations

import httpx

from app.core.config import get_settings


class PlacesNotConfiguredError(RuntimeError):
    pass


GENERIC_PLACE_CATEGORIES = {
    "business",
    "establishment",
    "point of interest",
    "restaurant",
    "food",
    "store",
    "service establishment",
    "local business",
}


def _best_category(primary_type_text: str | None, search_keyword: str | None) -> str | None:
    """Prefer the user's Places search term when Google's display category is broad.

    Example: searching "sushi restaurant" often returns a Google primary type of
    just "Restaurant". For site generation, "sushi restaurant" is more useful.
    """
    clean_primary = (primary_type_text or "").strip()
    clean_keyword = (search_keyword or "").strip()
    if clean_keyword and (not clean_primary or clean_primary.lower() in GENERIC_PLACE_CATEGORIES):
        return clean_keyword
    return clean_primary or clean_keyword or None


class GooglePlacesClient:
    """Small wrapper around Google Places Text Search.

    Google Places is used for lead discovery and basic business metadata. Email
    addresses should be found from the business's own public website, not from
    Places.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.google_places_api_key:
            raise PlacesNotConfiguredError("GOOGLE_PLACES_API_KEY is not configured")

    async def text_search(self, keyword: str, location: str, max_results: int = 20) -> list[dict]:
        query = f"{keyword} in {location}"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.settings.google_places_api_key or "",
            "X-Goog-FieldMask": ",".join(
                [
                    "places.id",
                    "places.displayName",
                    "places.formattedAddress",
                    "places.nationalPhoneNumber",
                    "places.internationalPhoneNumber",
                    "places.websiteUri",
                    "places.primaryType",
                    "places.primaryTypeDisplayName",
                    "places.types",
                    "places.googleMapsUri",
                ]
            ),
        }
        payload = {"textQuery": query, "pageSize": min(max_results, 20)}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://places.googleapis.com/v1/places:searchText",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return data.get("places", [])[:max_results]


def normalise_place(place: dict, city: str | None = None, search_keyword: str | None = None, search_location: str | None = None) -> dict:
    display_name = place.get("displayName") or {}
    primary_type = place.get("primaryTypeDisplayName") or {}
    primary_type_text = primary_type.get("text")
    raw_data = {
        **place,
        "searchKeyword": search_keyword,
        "searchLocation": search_location or city,
        "classificationCategory": _best_category(primary_type_text, search_keyword),
    }
    return {
        "place_id": place.get("id"),
        "name": display_name.get("text") or "Unknown business",
        # Prefer search term when Google gives a broad category. This prevents
        # a "sushi restaurant" search from degenerating into generic Restaurant,
        # and a "plumber" search from losing service-business context.
        "category": _best_category(primary_type_text, search_keyword),
        "phone": place.get("internationalPhoneNumber") or place.get("nationalPhoneNumber"),
        "website_url": place.get("websiteUri"),
        "address": place.get("formattedAddress"),
        "city": city,
        "source": "google_places",
        "raw_data": raw_data,
    }
