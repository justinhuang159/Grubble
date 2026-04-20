<script setup lang="ts">
import { computed, onMounted } from "vue";

import { useSessionStore } from "../stores/session";

const store = useSessionStore();

const matchMessage = computed(() => {
  const result = store.latestVoteResult;
  if (!result || !result.matched || !result.matched_restaurant_id) {
    return "";
  }
  return `Match found on restaurant #${result.matched_restaurant_id}`;
});

onMounted(async () => {
  if (!store.currentRestaurant) {
    await store.loadNextRestaurant();
  }
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
          <span v-if="store.currentRestaurant.price" class="metric-chip">{{ store.currentRestaurant.price }}</span>
          <span v-if="store.currentRestaurant.rating" class="metric-chip">{{ store.currentRestaurant.rating }} stars</span>
          <span v-if="store.currentRestaurant.review_count" class="metric-chip">
            {{ store.currentRestaurant.review_count }} reviews
          </span>
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
