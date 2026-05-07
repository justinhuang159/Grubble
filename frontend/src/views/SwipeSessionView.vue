<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

import { formatRestaurantPrice } from "../lib/restaurant";
import { useSessionStore } from "../stores/session";

const store = useSessionStore();
let socket: WebSocket | null = null;

const celebrating = ref(false);
const celebrationName = ref("");
const celebrationImage = ref<string | null>(null);
let celebrationTimer: ReturnType<typeof setTimeout> | null = null;

function triggerCelebration(name: string, imageUrl: string | null) {
  if (celebrating.value) return;
  celebrationName.value = name;
  celebrationImage.value = imageUrl;
  celebrating.value = true;
  celebrationTimer = setTimeout(() => {
    store.openResults();
  }, 3000);
}

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
      const message = JSON.parse(event.data) as {
        event?: string;
        restaurant_id?: number;
        restaurant_name?: string;
        restaurant_image_url?: string;
        yes_votes_for_restaurant?: number;
        votes_submitted_for_restaurant?: number;
        total_participants?: number;
      };
      if (message.event === "match_found") {
        triggerCelebration(message.restaurant_name ?? "your restaurant", message.restaurant_image_url ?? null);
      } else if (
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

// Fallback for the voter if WebSocket delivery is delayed
watch(() => store.latestVoteResult, (result) => {
  if (result?.matched && result.matched_restaurant_id && !celebrating.value) {
    triggerCelebration(store.currentRestaurant?.name ?? "your restaurant", store.currentRestaurant?.image_url ?? null);
  }
});

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
  if (celebrationTimer) clearTimeout(celebrationTimer);
});
</script>

<template>
  <Transition name="celebrate">
    <div
      v-if="celebrating"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm"
    >
      <div class="w-full max-w-sm overflow-hidden rounded-[2rem] bg-white shadow-2xl">
        <div class="relative h-48 bg-stone-100">
          <img
            v-if="celebrationImage"
            :src="celebrationImage"
            alt=""
            class="h-full w-full object-cover"
          />
          <div v-else class="flex h-full items-center justify-center text-7xl">🍽️</div>
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
          <p class="absolute bottom-3 left-4 right-4 truncate text-lg font-semibold text-white">
            {{ celebrationName }}
          </p>
        </div>
        <div class="px-6 pb-6 pt-5 text-center">
          <p class="text-xs font-semibold uppercase tracking-widest text-orange-700">unanimous match</p>
          <h2 class="mt-1 font-serif text-3xl text-stone-900">It's a match!</h2>
          <p class="mt-2 text-sm text-stone-500">Everyone said yes. Taking you to results…</p>
          <div class="mt-4 flex justify-center gap-1.5">
            <span class="h-1.5 w-6 animate-pulse rounded-full bg-orange-500" style="animation-delay: 0ms" />
            <span class="h-1.5 w-6 animate-pulse rounded-full bg-orange-400" style="animation-delay: 200ms" />
            <span class="h-1.5 w-6 animate-pulse rounded-full bg-orange-300" style="animation-delay: 400ms" />
          </div>
        </div>
      </div>
    </div>
  </Transition>

  <section class="glass-card">
    <div class="flex items-center justify-between">
      <h2 class="section-title text-stone-900">Swipe Deck</h2>
      <span class="status-pill">
        Room: {{ store.session?.room_code }}
      </span>
    </div>

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

<style scoped>
.celebrate-enter-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.celebrate-enter-from {
  opacity: 0;
  transform: scale(0.95);
}
</style>
