import axios from "axios";
import { supabase } from "./supabase";
import type {
  CreateSessionRequest,
  JoinSessionRequest,
  MySessionsResponse,
  NextRestaurantResponse,
  PopularDishItem,
  ReviewItem,
  SessionResultsResponse,
  SessionResponse,
  StartSessionRequest,
  VoteRequest,
  VoteResponse,
} from "../types";

export interface UpdateFiltersPayload {
  location_text?: string | null;
  cuisine?: string | null;
  price?: string | null;
  radius_meters?: number | null;
}

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const api = axios.create({
  baseURL,
  timeout: 10000,
});

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function createSession(payload: CreateSessionRequest): Promise<SessionResponse> {
  const { data } = await api.post<SessionResponse>("/sessions", payload);
  return data;
}

export async function joinSession(
  roomCode: string,
  payload: JoinSessionRequest,
): Promise<SessionResponse> {
  const { data } = await api.post<SessionResponse>(`/sessions/${roomCode}/join`, payload);
  return data;
}

export async function getSession(roomCode: string): Promise<SessionResponse> {
  const { data } = await api.get<SessionResponse>(`/sessions/${roomCode}`);
  return data;
}

export async function startSession(
  roomCode: string,
  payload: StartSessionRequest,
): Promise<SessionResponse> {
  const { data } = await api.post<SessionResponse>(`/sessions/${roomCode}/start`, payload);
  return data;
}

export async function getNextRestaurant(
  roomCode: string,
  userName: string,
): Promise<NextRestaurantResponse> {
  const { data } = await api.get<NextRestaurantResponse>(`/sessions/${roomCode}/restaurants/next`, {
    params: { user_name: userName },
  });
  return data;
}

export async function submitVote(
  roomCode: string,
  payload: VoteRequest,
): Promise<VoteResponse> {
  const { data } = await api.post<VoteResponse>(`/sessions/${roomCode}/votes`, payload);
  return data;
}

export async function getSessionResults(roomCode: string): Promise<SessionResultsResponse> {
  const { data } = await api.get<SessionResultsResponse>(`/sessions/${roomCode}/results`);
  return data;
}

export async function getReviews(
  roomCode: string,
  restaurantId: number,
): Promise<{ reviews: ReviewItem[] }> {
  const { data } = await api.get<{ reviews: ReviewItem[] }>(
    `/sessions/${roomCode}/restaurants/${restaurantId}/reviews`,
  );
  return data;
}

export async function validateLocation(locationText: string): Promise<{ valid: boolean }> {
  const { data } = await api.get<{ valid: boolean }>("/validate-location", {
    params: { location_text: locationText },
  });
  return data;
}

export async function getMySessions(): Promise<MySessionsResponse> {
  const { data } = await api.get<MySessionsResponse>("/sessions/my");
  return data;
}

export async function deleteSession(roomCode: string): Promise<void> {
  await api.delete(`/sessions/${roomCode}`);
}

export async function updateSessionFilters(
  roomCode: string,
  payload: UpdateFiltersPayload,
): Promise<SessionResponse> {
  const { data } = await api.patch<SessionResponse>(`/sessions/${roomCode}`, payload);
  return data;
}

export async function removeSessionParticipant(
  roomCode: string,
  userName: string,
): Promise<void> {
  await api.delete(`/sessions/${roomCode}/participants/${encodeURIComponent(userName)}`);
}

export async function getPopularDishes(
  roomCode: string,
  restaurantId: number,
): Promise<{ popular_dishes: PopularDishItem[] }> {
  const { data } = await api.get<{ popular_dishes: PopularDishItem[] }>(
    `/sessions/${roomCode}/restaurants/${restaurantId}/popular_dishes`,
  );
  return data;
}
