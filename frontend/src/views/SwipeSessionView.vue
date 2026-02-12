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
  <section class="rounded-xl bg-white p-6 shadow">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-slate-900">Swipe</h2>
      <span class="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
        Room: {{ store.session?.room_code }}
      </span>
    </div>

    <p v-if="matchMessage" class="mt-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
      {{ matchMessage }}
    </p>

    <div v-if="store.currentRestaurant" class="mt-4 rounded-lg border border-slate-200 p-5">
      <p class="text-lg font-semibold text-slate-900">{{ store.currentRestaurant.name }}</p>
      <p v-if="store.currentRestaurant.address" class="mt-1 text-sm text-slate-600">
        {{ store.currentRestaurant.address }}
      </p>
      <p class="mt-2 text-sm text-slate-600">
        <span v-if="store.currentRestaurant.price">{{ store.currentRestaurant.price }} </span>
        <span v-if="store.currentRestaurant.rating">• {{ store.currentRestaurant.rating }} stars</span>
      </p>

      <div class="mt-5 grid grid-cols-2 gap-3">
        <button
          :disabled="store.voteLoading"
          class="rounded-md bg-rose-600 px-4 py-2 font-medium text-white disabled:opacity-60"
          @click="store.vote('no')"
        >
          {{ store.voteLoading ? "Submitting..." : "No" }}
        </button>
        <button
          :disabled="store.voteLoading"
          class="rounded-md bg-emerald-600 px-4 py-2 font-medium text-white disabled:opacity-60"
          @click="store.vote('yes')"
        >
          {{ store.voteLoading ? "Submitting..." : "Yes" }}
        </button>
      </div>
    </div>

    <p v-else class="mt-4 rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-700">
      No more restaurants available right now.
    </p>
  </section>
</template>
