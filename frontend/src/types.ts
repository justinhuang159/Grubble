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

export interface PhotoItem {
  url: string;
  caption: string | null;
}

export interface HoursItem {
  day: string;
  hours: string;
}

export interface ReviewItem {
  text: string;
  rating: number;
  author_name: string;
  author_location: string | null;
  author_photo_url: string | null;
  created_at: string;
}

export interface PopularDishItem {
  display_name: string;
  review_count: number;
  photo_url: string | null;
  photo_count: number;
}

export interface RestaurantCard {
  id: number;
  name: string;
  image_url: string | null;
  address: string | null;
  price: string | null;
  rating: number | null;
  review_count: number | null;
  categories: string[];
  photos: PhotoItem[];
  hours: HoursItem[] | null;
  yelp_url: string | null;
  phone: string | null;
  short_address: string | null;
  popular_dishes?: PopularDishItem[] | null;
  reviews?: ReviewItem[] | null;
}

export interface NextRestaurantResponse {
  restaurant: RestaurantCard | null;
  total_participants: number;
  yes_votes: number;
  total_votes: number;
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
  next_yes_votes: number;
  next_total_votes: number;
}

export interface SessionResultItem {
  restaurant: RestaurantCard;
  yes_votes: number;
  total_votes: number;
}

export interface SessionResultsResponse {
  total_participants: number;
  results: SessionResultItem[];
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
  owner_user_id: string | null;
}

export interface SessionSummary {
  room_code: string;
  host_name: string;
  status: SessionStatus;
  location_text: string | null;
  created_at: string;
  participant_count: number;
}

export interface MySessionsResponse {
  hosted: SessionSummary[];
  joined: SessionSummary[];
}
