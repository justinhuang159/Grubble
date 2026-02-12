import { defineStore } from "pinia";
import { computed, ref } from "vue";
import axios from "axios";

import {
  createSession,
  getNextRestaurant,
  getSession,
  joinSession,
  startSession,
  submitVote,
} from "../lib/api";
import type { CreateSessionRequest, RestaurantCard, SessionResponse, VoteResponse } from "../types";

export const useSessionStore = defineStore("session", () => {
  const session = ref<SessionResponse | null>(null);
  const currentUser = ref<string>("");
  const loading = ref(false);
  const voteLoading = ref(false);
  const error = ref<string>("");
  const currentRestaurant = ref<RestaurantCard | null>(null);
  const latestVoteResult = ref<VoteResponse | null>(null);

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

  function setErrorFromUnknown(err: unknown): void {
    if (axios.isAxiosError(err)) {
      const detail = err.response?.data?.detail;
      error.value =
        typeof detail === "string"
          ? detail
          : `Request failed (${err.response?.status ?? "network error"}).`;
      return;
    }
    error.value = "Request failed. Please try again.";
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
    currentRestaurant.value = null;
    latestVoteResult.value = null;
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
    currentRestaurant.value = null;
    latestVoteResult.value = null;
  }

  function setSession(data: SessionResponse): void {
    session.value = data;
  }

  async function loadNextRestaurant(): Promise<void> {
    if (!session.value || !currentUser.value) {
      return;
    }
    error.value = "";
    try {
      const data = await getNextRestaurant(session.value.room_code, currentUser.value);
      currentRestaurant.value = data.restaurant;
    } catch (err) {
      setErrorFromUnknown(err);
      throw err;
    }
  }

  async function vote(decision: "yes" | "no"): Promise<void> {
    if (!session.value || !currentUser.value || !currentRestaurant.value) {
      return;
    }
    voteLoading.value = true;
    error.value = "";
    try {
      const data = await submitVote(session.value.room_code, {
        user_name: currentUser.value,
        restaurant_id: currentRestaurant.value.id,
        decision,
      });
      latestVoteResult.value = data;
      currentRestaurant.value = data.next_restaurant;
    } catch (err) {
      setErrorFromUnknown(err);
      throw err;
    } finally {
      voteLoading.value = false;
    }
  }

  return {
    session,
    currentUser,
    loading,
    voteLoading,
    error,
    currentRestaurant,
    latestVoteResult,
    isHost,
    create,
    join,
    refresh,
    start,
    setSession,
    loadNextRestaurant,
    vote,
  };
});
