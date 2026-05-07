<script setup lang="ts">
import { computed, onMounted, onUnmounted } from "vue";

import { formatRestaurantPrice } from "../lib/restaurant";
import { useSessionStore } from "../stores/session";

const store = useSessionStore();
let socket: WebSocket | null = null;

const matchMessage = computed(() => {
  const result = store.latestVoteResult;
  if (!result || !result.matched || !result.matched_restaurant_id) {
    return "";
  }
  return `Match found on restaurant #${result.matched_restaurant_id}`;
});

const progressPercent = computed(() => {
  const p = store.voteProgress;
  if (!p || p.total_participants === 0) return 0;
  return Math.round((p.total_votes / p.total_participants) * 100);
});

function buildWsUrl(roomCode: string): string {
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
  const wsBase = apiBase.replace(/^http/, "ws");
  return `${wsBase}/ws/sessions/${roomCode}`;
}

function connectSocket(roomCode: string) {
  socket = new WebSocket(buildWsUrl(roomCode));
  socket.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data) as { event?: string; restaurant_id?: number; yes_votes_for_restaurant?: number; votes_submitted_for_restaurant?: number; total_participants?: number };
      if (
        message.event === "vote_progress" &&
        message.restaurant_id != null &&
        message.yes_votes_for_restaurant != null &&
        message.votes_submitted_for_restaurant != null &&
        message.total_participants != null
      ) {
        store.updateVoteProgress({
          restaurant_id: message.restaurant_id,
          yes_votes_for_restaurant: message.yes_votes_for_restaurant,
          votes_submitted_for_restaurant: message.votes_submitted_for_restaurant,
          total_participants: message.total_participants,
        });
      }
    } catch {
      // ignore malformed messages
    }
  };
}

onMounted(async () => {
  if (!store.currentRestaurant) {
    await store.loadNextRestaurant();
  }
  if (store.session) {
    connectSocket(store.session.room_code);
  }
});

onUnmounted(() => {
  socket?.close();
});
</script>

<template>
  <section class="glass-card">
    <div class="flex items-center justify-between">
      <h2 class="section-title text-stone-900">Swipe Deck</h2>
      <span class="status-pill">
        Room: {{ store.session?.room_code }}
      </span>
    </div>

    <p v-if="matchMessage" class="soft-alert mt-4 bg-emerald-50 text-emerald-700">
      {{ matchMessage }}
    </p>

    <div class="mt-4">
      <button
        class="app-button-secondary"
        :disabled="store.resultsLoading"
        @click="store.openResults"
      >
        {{ store.resultsLoading ? "Loading..." : "View Results" }}
      </button>
    </div>

    <div v-if="store.currentRestaurant" class="mt-6 overflow-hidden rounded-[1.75rem] border border-orange-950/10 bg-white/70 p-4 shadow-[0_20px_40px_rgba(28,25,23,0.08)]">
      <img
        v-if="store.currentRestaurant.image_url"
        :src="store.currentRestaurant.image_url"
        :alt="store.currentRestaurant.name"
        class="restaurant-image"
      />
      <div v-else class="restaurant-image flex items-end p-5 text-white">
        <p class="text-xl font-semibold">{{ store.currentRestaurant.name }}</p>
      </div>

      <div class="mt-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-2xl font-semibold text-stone-900">{{ store.currentRestaurant.name }}</p>
          <p v-if="store.currentRestaurant.address" class="mt-2 text-sm leading-6 text-stone-600">
        {{ store.currentRestaurant.address }}
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <span v-if="store.currentRestaurant.price" class="metric-chip">
            {{ formatRestaurantPrice(store.currentRestaurant.price) }}
          </span>
          <span v-if="store.currentRestaurant.rating" class="metric-chip">{{ store.currentRestaurant.rating }} stars</span>
          <span v-if="store.currentRestaurant.review_count" class="metric-chip">
            {{ store.currentRestaurant.review_count }} reviews
          </span>
        </div>
      </div>

      <div v-if="store.voteProgress" class="mt-4 rounded-2xl bg-stone-50/80 px-3 py-2.5">
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-xs font-medium text-stone-500">{{ store.voteProgress.total_votes }}/{{ store.voteProgress.total_participants }} voted</span>
          <span class="text-xs font-semibold text-emerald-700">{{ store.voteProgress.yes_votes }} yes</span>
        </div>
        <div class="h-1.5 w-full rounded-full bg-stone-200">
          <div
            class="h-1.5 rounded-full bg-orange-500 transition-all duration-300"
            :style="{ width: progressPercent + '%' }"
          />
        </div>
      </div>

      <div class="mt-5 grid grid-cols-2 gap-3">
        <button
          :disabled="store.voteLoading"
          class="rounded-full bg-rose-600 px-4 py-3 font-semibold text-white transition hover:bg-rose-500 disabled:opacity-60"
          @click="store.vote('no')"
        >
          {{ store.voteLoading ? "Submitting..." : "No" }}
        </button>
        <button
          :disabled="store.voteLoading"
          class="rounded-full bg-emerald-600 px-4 py-3 font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-60"
          @click="store.vote('yes')"
        >
          {{ store.voteLoading ? "Submitting..." : "Yes" }}
        </button>
      </div>
    </div>

    <p v-else class="soft-alert mt-4 bg-stone-100 text-stone-700">
      No more restaurants available right now.
    </p>
  </section>
</template>
