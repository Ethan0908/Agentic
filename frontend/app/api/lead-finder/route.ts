import { NextResponse } from 'next/server';
import { createClient } from '../../../lib/client-store';

type NewPlace = {
  id?: string;
  name?: string;
  displayName?: { text?: string; languageCode?: string };
  formattedAddress?: string;
  nationalPhoneNumber?: string;
  internationalPhoneNumber?: string;
  websiteUri?: string;
  googleMapsUri?: string;
  types?: string[];
  primaryType?: string;
  primaryTypeDisplayName?: { text?: string; languageCode?: string };
  rating?: number;
  userRatingCount?: number;
  photos?: { name?: string }[];
};

function apiKey() {
  return process.env.GOOGLE_PLACES_API_KEY || process.env.GOOGLE_MAPS_API_KEY || '';
}

function text(value: unknown) {
  return String(value || '').trim();
}

function cleanType(value: string) {
  return value.replace(/_/g, ' ').trim();
}

function leadType(place: NewPlace, fallback: string) {
  return text(place.primaryTypeDisplayName?.text)
    || cleanType(text(place.primaryType))
    || cleanType((place.types || []).find((item) => !['point_of_interest', 'establishment'].includes(item)) || '')
    || fallback;
}

function photoUrls(place: NewPlace, key: string) {
  return (place.photos || [])
    .map((photo) => photo.name)
    .filter(Boolean)
    .slice(0, 4)
    .map((name) => `https://places.googleapis.com/v1/${String(name)}/media?maxWidthPx=1400&key=${encodeURIComponent(key)}`);
}

async function searchPlacesNew(query: string, location: string, limit: number, key: string): Promise<NewPlace[]> {
  const response = await fetch('https://places.googleapis.com/v1/places:searchText', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Goog-Api-Key': key,
      'X-Goog-FieldMask': [
        'places.id',
        'places.name',
        'places.displayName',
        'places.formattedAddress',
        'places.nationalPhoneNumber',
        'places.internationalPhoneNumber',
        'places.websiteUri',
        'places.googleMapsUri',
        'places.types',
        'places.primaryType',
        'places.primaryTypeDisplayName',
        'places.rating',
        'places.userRatingCount',
        'places.photos',
      ].join(','),
    },
    body: JSON.stringify({
      textQuery: [query, location].filter(Boolean).join(' in '),
      maxResultCount: Math.max(1, Math.min(limit, 20)),
    }),
    cache: 'no-store',
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error?.message || payload.error_message || 'Places API New request failed.');
  }
  return Array.isArray(payload.places) ? payload.places : [];
}

function toLead(place: NewPlace, query: string, location: string, key: string) {
  const rating = place.rating ? `${place.rating} rating` : '';
  const reviews = place.userRatingCount ? `${place.userRatingCount} Google reviews` : '';
  const address = text(place.formattedAddress);
  const notes = [query, location, rating, reviews, address].filter(Boolean).join(' • ');

  return {
    name: text(place.displayName?.text),
    businessType: leadType(place, query),
    city: location,
    serviceArea: location,
    website: text(place.websiteUri || place.googleMapsUri),
    email: '',
    phone: text(place.nationalPhoneNumber || place.internationalPhoneNumber),
    notes,
    photos: photoUrls(place, key),
    status: 'lead' as const,
  };
}

export async function POST(request: Request) {
  const body = await request.json();
  const query = text(body.query);
  const location = text(body.location);
  const limit = Math.max(1, Math.min(Number(body.limit || 20) || 20, 20));
  const key = apiKey();

  if (!key) {
    return NextResponse.json({ error: 'Google Places key is missing. Set GOOGLE_PLACES_API_KEY or GOOGLE_MAPS_API_KEY in the Pi environment.' }, { status: 500 });
  }

  if (!query) {
    return NextResponse.json({ error: 'Enter a business type or niche to search.' }, { status: 400 });
  }

  const places = await searchPlacesNew(query, location, limit, key);
  const created = [];

  for (const place of places) {
    const lead = toLead(place, query, location, key);
    if (!lead.name) continue;
    created.push(await createClient(lead));
  }

  return NextResponse.json({ created, count: created.length });
}
