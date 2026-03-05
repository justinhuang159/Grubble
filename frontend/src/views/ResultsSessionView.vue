<script setup lang="ts">
import { computed, onMounted } from "vue";

import { useSessionStore } from "../stores/session";

const store = useSessionStore();

const rankedResults = computed(() => store.results?.results ?? []);

onMounted(async () => {
  if (!store.results) {
    await store.loadResults();
  }
});
</script>

<template>
  <section class="rounded-xl bg-white p-6 shadow">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-slate-900">Session Results</h2>
        <p class="mt-1 text-sm text-slate-600">Ranked by yes votes (highest to lowest)</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="rounded-md bg-slate-200 px-3 py-2 text-sm font-medium text-slate-800 hover:bg-slate-300"
          @click="store.closeResults"
        >
          Back to Swipe
        </button>
        <button
          class="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
          @click="store.resetState"
        >
          Start New Session
        </button>
      </div>
    </div>

    <p v-if="store.resultsLoading" class="mt-4 text-sm text-slate-600">Loading results...</p>

    <div v-else-if="rankedResults.length > 0" class="mt-4 space-y-3">
      <article
        v-for="(item, idx) in rankedResults"
        :key="item.restaurant.id"
        class="rounded-lg border border-slate-200 p-4"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">#{{ idx + 1 }}</p>
            <p class="text-lg font-semibold text-slate-900">{{ item.restaurant.name }}</p>
            <p v-if="item.restaurant.address" class="mt-1 text-sm text-slate-600">
              {{ item.restaurant.address }}
            </p>
            <p class="mt-2 text-sm text-slate-600">
              <span v-if="item.restaurant.price">{{ item.restaurant.price }} </span>
              <span v-if="item.restaurant.rating">• {{ item.restaurant.rating }} stars</span>
            </p>
          </div>
          <div class="rounded-md bg-emerald-50 px-3 py-2 text-right">
            <p class="text-xs text-emerald-700">Yes votes</p>
            <p class="text-lg font-semibold text-emerald-800">{{ item.yes_votes }}</p>
            <p class="text-xs text-emerald-700">of {{ store.results?.total_participants ?? 0 }} people</p>
          </div>
        </div>
        <p class="mt-2 text-xs text-slate-500">Total submitted votes: {{ item.total_votes }}</p>
      </article>
    </div>

    <p v-else class="mt-4 rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-700">
      No results yet. Votes will appear after participants start swiping.
    </p>
  </section>
</template>
