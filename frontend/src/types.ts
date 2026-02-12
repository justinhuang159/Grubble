export type SessionStatus = "waiting" | "active" | "paused" | "ended";

export interface CreateSessionRequest {
  host_name: string;
  cuisine?: string;
  price?: string;
  radius_miles?: number;
  radius_meters?: number;
  location_text: string;
}

export interface JoinSessionRequest {
  user_name: string;
}

export interface StartSessionRequest {
  host_name: string;
}

export interface RestaurantCard {
  id: number;
  name: string;
  image_url: string | null;
  address: string | null;
  price: string | null;
  rating: number | null;
  review_count: number | null;
}

export interface NextRestaurantResponse {
  restaurant: RestaurantCard | null;
}

export interface VoteRequest {
  user_name: string;
  restaurant_id: number;
  decision: "yes" | "no";
}

export interface VoteResponse {
  duplicate: boolean;
  matched: boolean;
  matched_restaurant_id: number | null;
  total_participants: number;
  votes_submitted_for_restaurant: number;
  yes_votes_for_restaurant: number;
  next_restaurant: RestaurantCard | null;
}

export interface SessionResponse {
  id: string;
  room_code: string;
  host_name: string;
  status: SessionStatus;
  cuisine: string | null;
  price: string | null;
  radius_meters: number | null;
  location_text: string | null;
  participants: string[];
}
