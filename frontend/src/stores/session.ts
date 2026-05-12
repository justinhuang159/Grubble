import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";
import axios from "axios";
import { useAuthStore } from "./auth";

import {
  createSession,
  getNextRestaurant,
  getSessionResults,
  getSession,
  joinSession,
  removeSessionParticipant,
  startSession,
  submitVote,
  updateSessionFilters,
} from "../lib/api";
import type { UpdateFiltersPayload } from "../lib/api";
import type {
  CreateSessionRequest,
  RestaurantCard,
  SessionResponse,
  SessionResultsResponse,
  VoteResponse,
} from "../types";

export const useSessionStore = defineStore("session", () => {
  const STORAGE_KEY = "grubble.session.v1";

  const session = ref<SessionResponse | null>(null);
  const currentUser = ref<string>("");
  const loading = ref(false);
  const voteLoading = ref(false);
  const error = ref<string>("");
  const currentRestaurant = ref<RestaurantCard | null>(null);
  const latestVoteResult = ref<VoteResponse | null>(null);
  const results = ref<SessionResultsResponse | null>(null);
  const resultsLoading = ref(false);
  const showResults = ref(false);
  const voteProgress = ref<{ yes_votes: number; total_votes: number; total_participants: number } | null>(null);
  const kickNotification = ref<string | null>(null);

  function hydrateFromStorage(): void {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return;
    }
    try {
      const parsed = JSON.parse(raw) as {
        session?: SessionResponse | null;
        currentUser?: string;
        showResults?: boolean;
      };
      session.value = parsed.session ?? null;
      currentUser.value = parsed.currentUser ?? "";
      showResults.value = Boolean(parsed.showResults);
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  const auth = useAuthStore();

  const isHost = computed(() => {
    if (!session.value) return false;
    if (auth.user?.id && session.value.owner_user_id) {
      return session.value.owner_user_id === auth.user.id;
    }
    return Boolean(currentUser.value) && session.value.host_name === currentUser.value;
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
    results.value = null;
    showResults.value = false;
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
    results.value = null;
    showResults.value = false;
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
      voteProgress.value = data.restaurant
        ? { yes_votes: data.yes_votes, total_votes: data.total_votes, total_participants: data.total_participants }
        : null;
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
      voteProgress.value = data.next_restaurant
        ? { yes_votes: data.next_yes_votes, total_votes: data.next_total_votes, total_participants: data.total_participants }
        : null;
    } catch (err) {
      setErrorFromUnknown(err);
      throw err;
    } finally {
      voteLoading.value = false;
    }
  }

  function updateVoteProgress(data: {
    restaurant_id: number;
    yes_votes_for_restaurant: number;
    votes_submitted_for_restaurant: number;
    total_participants: number;
  }): void {
    if (currentRestaurant.value?.id === data.restaurant_id) {
      voteProgress.value = {
        yes_votes: data.yes_votes_for_restaurant,
        total_votes: data.votes_submitted_for_restaurant,
        total_participants: data.total_participants,
      };
    }
  }

  async function loadResults(): Promise<void> {
    if (!session.value) {
      return;
    }
    resultsLoading.value = true;
    error.value = "";
    try {
      const data = await getSessionResults(session.value.room_code);
      results.value = data;
    } catch (err) {
      setErrorFromUnknown(err);
      throw err;
    } finally {
      resultsLoading.value = false;
    }
  }

  async function refreshResults(): Promise<void> {
    if (!session.value) return;
    try {
      const data = await getSessionResults(session.value.room_code);
      results.value = data;
    } catch {
      // silently ignore — stale data is better than an error flash
    }
  }

  async function openResults(): Promise<void> {
    await loadResults();
    showResults.value = true;
  }

  function closeResults(): void {
    showResults.value = false;
  }

  async function updateFilters(roomCode: string, payload: UpdateFiltersPayload): Promise<void> {
    const data = await handle(() => updateSessionFilters(roomCode, payload));
    if (session.value?.room_code === roomCode) session.value = data;
  }

  async function removeParticipant(roomCode: string, userName: string): Promise<void> {
    await handle(() => removeSessionParticipant(roomCode, userName));
    await refresh();
  }

  function resetState(): void {
    session.value = null;
    currentUser.value = "";
    loading.value = false;
    voteLoading.value = false;
    error.value = "";
    currentRestaurant.value = null;
    latestVoteResult.value = null;
    results.value = null;
    resultsLoading.value = false;
    showResults.value = false;
  }

  hydrateFromStorage();

  watch(
    [session, currentUser, showResults],
    () => {
      if (!session.value || !currentUser.value) {
        localStorage.removeItem(STORAGE_KEY);
        return;
      }
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          session: session.value,
          currentUser: currentUser.value,
          showResults: showResults.value,
        }),
      );
    },
    { deep: true },
  );

  return {
    session,
    currentUser,
    loading,
    voteLoading,
    error,
    currentRestaurant,
    latestVoteResult,
    results,
    resultsLoading,
    showResults,
    voteProgress,
    kickNotification,
    isHost,
    create,
    join,
    refresh,
    start,
    setSession,
    loadNextRestaurant,
    vote,
    updateVoteProgress,
    loadResults,
    refreshResults,
    openResults,
    closeResults,
    resetState,
    updateFilters,
    removeParticipant,
  };
});
