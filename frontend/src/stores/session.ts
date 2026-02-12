import { defineStore } from "pinia";
import { computed, ref } from "vue";
import axios from "axios";

import { createSession, getSession, joinSession, startSession } from "../lib/api";
import type { CreateSessionRequest, SessionResponse } from "../types";

export const useSessionStore = defineStore("session", () => {
  const session = ref<SessionResponse | null>(null);
  const currentUser = ref<string>("");
  const loading = ref(false);
  const error = ref<string>("");

  const isHost = computed(() => {
    if (!session.value || !currentUser.value) {
      return false;
    }
    return session.value.host_name === currentUser.value;
  });

  async function handle<T>(op: () => Promise<T>): Promise<T> {
    loading.value = true;
    error.value = "";
    try {
      return await op();
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        error.value =
          typeof detail === "string"
            ? detail
            : `Request failed (${err.response?.status ?? "network error"}).`;
      } else {
        error.value = "Request failed. Please try again.";
      }
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function create(payload: CreateSessionRequest): Promise<void> {
    const normalized: CreateSessionRequest = {
      host_name: payload.host_name.trim(),
      location_text: payload.location_text.trim(),
      cuisine: payload.cuisine?.trim() || undefined,
      price: payload.price?.trim() || undefined,
      radius_meters:
        typeof payload.radius_miles === "number"
          ? Math.round(payload.radius_miles * 1609.34)
          : payload.radius_meters,
    };
    const data = await handle(() => createSession(normalized));
    session.value = data;
    currentUser.value = normalized.host_name;
  }

  async function join(roomCode: string, userName: string): Promise<void> {
    const trimmedRoomCode = roomCode.trim().toUpperCase();
    const trimmedName = userName.trim();
    const data = await handle(() => joinSession(trimmedRoomCode, { user_name: trimmedName }));
    session.value = data;
    currentUser.value = trimmedName;
  }

  async function refresh(): Promise<void> {
    if (!session.value) {
      return;
    }
    const data = await handle(() => getSession(session.value!.room_code));
    session.value = data;
  }

  async function start(): Promise<void> {
    if (!session.value) {
      return;
    }
    const data = await handle(() =>
      startSession(session.value!.room_code, { host_name: currentUser.value }),
    );
    session.value = data;
  }

  function setSession(data: SessionResponse): void {
    session.value = data;
  }

  return {
    session,
    currentUser,
    loading,
    error,
    isHost,
    create,
    join,
    refresh,
    start,
    setSession,
  };
});
