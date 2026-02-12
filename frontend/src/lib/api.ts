import axios from "axios";
import type {
  CreateSessionRequest,
  JoinSessionRequest,
  SessionResponse,
  StartSessionRequest,
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
