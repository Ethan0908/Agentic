import { NextResponse } from 'next/server';
import { createClient } from '../../../lib/client-store';

type PlaceSearchResult = {
  place_id?: string;
  name?: string;
  formatted_address?: string;
  types?: string[];
  rating?: number;
  user_ratings_total?: number;
  photos?: { photo_reference?: string }[];
};

type PlaceDetailsResult = {
  name?: string;
  formatted_address?: string;
  formatted_phone_number?: string;
  international_phone_number?: string;
  website?: string;
  url?: string;
  types?: string[];
  rating?: number;
  user_ratings_total?: number;
  photos?: { photo_reference?: string }[];
};

function apiKey() {
  return process.env.GOOGLE_PLACES_API_KEY || process.env.GOOGLE_MAPS_API_KEY || '';
}

function text(value: unknown) {
  return String(value || '').trim();
}

function leadType(place: PlaceSearchResult | PlaceDetailsResult, fallback: string) {
  const types = Array.isArray(place.types) ? place.types : [];
  const cleaned = types
    .filter((item) => !['point_of_interest', 'establishment'].includes(item))
    .map((item) => item.replace(/_/g, ' '));
  return cleaned[0] || fallback;
}

function photoUrls(place: PlaceSearchResult | PlaceDetailsResult, key: string) {
  const photos = Array.isArray(place.photos) ? place.photos : [];
  return photos
    .map((photo) => photo.photo_reference)
    .filter(Boolean)
    .slice(0, 4)
    .map((reference) => `https://maps.googleapis.com/maps/api/place/photo?maxwidth=1400&photoreference=${encodeURIComponent(String(reference))}&key=${encodeURIComponent(key)}`);
}

async function googleJson(url: URL) {
  const response = await fetch(url, { cache: 'no-store' });
  const payload = await response.json();
  if (!response.ok || (payload.status && !['OK', 'ZERO_RESULTS'].includes(payload.status))) {
    throw new Error(payload.error_message || payload.status || 'Google Places request failed.');
  }
  return payload;
}

async function searchPlaces(query: string, location: string, limit: number, key: string): Promise<PlaceSearchResult[]> {
  const url = new URL('https://maps.googleapis.com/maps/api/place/textsearch/json');
  url.searchParams.set('query', [query, location].filter(Boolean).join(' in '));
  url.searchParams.set('key', key);
  const payload = await googleJson(url);
  const results = Array.isArray(payload.results) ? payload.results : [];
  return results.slice(0, limit);
}

async function placeDetails(placeId: string, key: string): Promise<PlaceDetailsResult> {
  const url = new URL('https://maps.googleapis.com/maps/api/place/details/json');
  url.searchParams.set('place_id', placeId);
  url.searchParams.set('fields', 'name,formatted_address,formatted_phone_number,international_phone_number,website,url,types,rating,user_ratings_total,photos');
  url.searchParams.set('key', key);
  const payload = await googleJson(url);
  return payload.result || {};
}

function toLead(place: PlaceSearchResult, details: PlaceDetailsResult, query: string, location: string, key: string) {
  const merged = { ...place, ...details };
  const rating = merged.rating ? `${merged.rating} rating` : '';
  const reviews = merged.user_ratings_total ? `${merged.user_ratings_total} Google reviews` : '';
  const address = text(merged.formatted_address);
  const notes = [query, location, rating, reviews, address].filter(Boolean).join(' • ');

  return {
    name: text(merged.name),
    businessType: leadType(merged, query),
    city: location,
    serviceArea: location,
    website: text(merged.website || merged.url),
    email: '',
    phone: text(merged.formatted_phone_number || merged.international_phone_number),
    notes,
    photos: photoUrls(merged, key),
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

  const places = await searchPlaces(query, location, limit, key);
  const created = [];

  for (const place of places) {
    if (!place.place_id) continue;
    const details = await placeDetails(place.place_id, key);
    const lead = toLead(place, details, query, location, key);
    if (!lead.name) continue;
    created.push(await createClient(lead));
  }

  return NextResponse.json({ created, count: created.length });
}
