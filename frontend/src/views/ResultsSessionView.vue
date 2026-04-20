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
  <section class="glass-card">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h2 class="section-title text-stone-900">Session Results</h2>
        <p class="section-copy">Ranked by yes votes, with the strongest picks surfaced first.</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="app-button-secondary"
          @click="store.closeResults"
        >
          Back to Swipe
        </button>
        <button
          class="app-button"
          @click="store.resetState"
        >
          Start New Session
        </button>
      </div>
    </div>

    <p v-if="store.resultsLoading" class="section-copy mt-4">Loading results...</p>

    <div v-else-if="rankedResults.length > 0" class="mt-4 space-y-3">
      <article
        v-for="(item, idx) in rankedResults"
        :key="item.restaurant.id"
        class="overflow-hidden rounded-[1.75rem] border border-orange-950/10 bg-white/72 p-4 shadow-[0_18px_34px_rgba(28,25,23,0.06)]"
      >
        <div class="grid gap-4 sm:grid-cols-[12rem_minmax(0,1fr)]">
          <img
            v-if="item.restaurant.image_url"
            :src="item.restaurant.image_url"
            :alt="item.restaurant.name"
            class="restaurant-image h-40"
          />
          <div v-else class="restaurant-image flex h-40 items-end p-4 text-white">
            <p class="text-lg font-semibold">{{ item.restaurant.name }}</p>
          </div>
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-orange-700">#{{ idx + 1 }}</p>
              <p class="mt-2 text-2xl font-semibold text-stone-900">{{ item.restaurant.name }}</p>
              <p v-if="item.restaurant.address" class="mt-2 text-sm leading-6 text-stone-600">
              {{ item.restaurant.address }}
              </p>
              <div class="mt-3 flex flex-wrap gap-2">
                <span v-if="item.restaurant.price" class="metric-chip">{{ item.restaurant.price }}</span>
                <span v-if="item.restaurant.rating" class="metric-chip">{{ item.restaurant.rating }} stars</span>
                <span v-if="item.restaurant.review_count" class="metric-chip">
                  {{ item.restaurant.review_count }} reviews
                </span>
              </div>
            </div>
            <div class="rounded-2xl bg-emerald-50 px-4 py-3 text-right">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-700">Yes votes</p>
              <p class="mt-1 text-2xl font-semibold text-emerald-800">{{ item.yes_votes }}</p>
              <p class="text-xs text-emerald-700">of {{ store.results?.total_participants ?? 0 }} people</p>
            </div>
          </div>
        </div>
        <p class="mt-4 text-xs font-medium uppercase tracking-[0.2em] text-stone-500">
          Total submitted votes: {{ item.total_votes }}
        </p>
      </article>
    </div>

    <p v-else class="soft-alert mt-4 bg-stone-100 text-stone-700">
      No results yet. Votes will appear after participants start swiping.
    </p>
  </section>
</template>
