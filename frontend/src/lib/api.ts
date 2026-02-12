import axios from "axios";
import type {
  CreateSessionRequest,
  JoinSessionRequest,
  NextRestaurantResponse,
  SessionResponse,
  StartSessionRequest,
  VoteRequest,
  VoteResponse,
} from "../types";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const api = axios.create({
  baseURL,
  timeout: 10000,
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
