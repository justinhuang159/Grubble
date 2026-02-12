import { defineStore } from "pinia";
import { computed, ref } from "vue";
import axios from "axios";

import { createSession, getSession, joinSession, startSession } from "../lib/api";
import type { SessionResponse } from "../types";

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

  async function create(hostName: string): Promise<void> {
    const trimmed = hostName.trim();
    const data = await handle(() => createSession({ host_name: trimmed }));
    session.value = data;
    currentUser.value = trimmed;
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
  };
});
