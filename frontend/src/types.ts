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
