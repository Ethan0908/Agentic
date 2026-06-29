from __future__ import annotations

import httpx

from app.core.config import get_settings


class PlacesNotConfiguredError(RuntimeError):
    pass


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
                    "places.primaryTypeDisplayName",
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


def normalise_place(place: dict, city: str | None = None) -> dict:
    display_name = place.get("displayName") or {}
    primary_type = place.get("primaryTypeDisplayName") or {}
    return {
        "place_id": place.get("id"),
        "name": display_name.get("text") or "Unknown business",
        "category": primary_type.get("text"),
        "phone": place.get("internationalPhoneNumber") or place.get("nationalPhoneNumber"),
        "website_url": place.get("websiteUri"),
        "address": place.get("formattedAddress"),
        "city": city,
        "source": "google_places",
        "raw_data": place,
    }
