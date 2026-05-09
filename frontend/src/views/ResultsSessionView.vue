<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import { formatRestaurantPrice } from "../lib/restaurant";
import { useSessionStore } from "../stores/session";
import type { RestaurantCard } from "../types";

const store = useSessionStore();

const rankedResults = computed(() => store.results?.results ?? []);

const PAGE_SIZE = 10;
const currentPage = ref(1);

const totalPages = computed(() => Math.ceil(rankedResults.value.length / PAGE_SIZE));

const pagedResults = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE;
  return rankedResults.value.slice(start, start + PAGE_SIZE);
});

const pageNumbers = computed<(number | "…")[]>(() => {
  const total = totalPages.value;
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const p = currentPage.value;
  if (p <= 4) return [1, 2, 3, 4, 5, "…", total];
  if (p >= total - 3) return [1, "…", total - 4, total - 3, total - 2, total - 1, total];
  return [1, "…", p - 1, p, p + 1, "…", total];
});

// Per-card carousel state keyed by restaurant id
const photoIndexes = ref<Record<number, number>>({});

function getPhotoIndex(id: number): number {
  return photoIndexes.value[id] ?? 0;
}

function setPhotoIndex(id: number, i: number) {
  photoIndexes.value[id] = i;
}

function photosFor(r: RestaurantCard) {
  if (r.photos.length > 0) return r.photos;
  if (r.image_url) return [{ url: r.image_url, caption: null }];
  return [];
}

// Lightbox
const lightboxOpen = ref(false);
const lightboxPhotos = ref<{ url: string; caption: string | null }[]>([]);
const lightboxIndex = ref(0);

function openLightbox(photos: { url: string; caption: string | null }[], index: number) {
  lightboxPhotos.value = photos;
  lightboxIndex.value = index;
  lightboxOpen.value = true;
}

function closeLightbox() {
  lightboxOpen.value = false;
}

function lightboxPrev() {
  lightboxIndex.value = (lightboxIndex.value - 1 + lightboxPhotos.value.length) % lightboxPhotos.value.length;
}

function lightboxNext() {
  lightboxIndex.value = (lightboxIndex.value + 1) % lightboxPhotos.value.length;
}

function handleKeydown(e: KeyboardEvent) {
  if (!lightboxOpen.value) return;
  if (e.key === "Escape") closeLightbox();
  else if (e.key === "ArrowLeft") lightboxPrev();
  else if (e.key === "ArrowRight") lightboxNext();
}

let socket: WebSocket | null = null;

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
        yes_votes_for_restaurant?: number;
        votes_submitted_for_restaurant?: number;
      };
      if (
        message.event === "vote_progress" &&
        message.restaurant_id != null &&
        message.yes_votes_for_restaurant != null &&
        message.votes_submitted_for_restaurant != null &&
        store.results
      ) {
        const item = store.results.results.find(
          (r) => r.restaurant.id === message.restaurant_id,
        );
        if (item) {
          item.yes_votes = message.yes_votes_for_restaurant!;
          item.total_votes = message.votes_submitted_for_restaurant!;
          store.results.results.sort((a, b) => {
            if (b.yes_votes !== a.yes_votes) return b.yes_votes - a.yes_votes;
            if (b.total_votes !== a.total_votes) return b.total_votes - a.total_votes;
            return a.restaurant.id - b.restaurant.id;
          });
        }
      }
    } catch {
      // ignore malformed messages
    }
  };
}

onMounted(async () => {
  window.addEventListener("keydown", handleKeydown);
  if (!store.results) {
    await store.loadResults();
  }
  if (store.session) {
    connectSocket(store.session.room_code);
  }
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
  socket?.close();
});
</script>

<template>
  <!-- Photo lightbox — teleported to body to escape hero-panel's backdrop-filter containing block -->
  <Teleport to="body">
  <Transition name="lightbox">
    <div
      v-if="lightboxOpen"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/90 backdrop-blur-md"
      @click.self="closeLightbox"
    >
      <div class="relative mx-4 w-full max-w-3xl">
        <div class="relative overflow-hidden rounded-2xl bg-black shadow-2xl">
          <img
            :src="lightboxPhotos[lightboxIndex].url.replace('/l.', '/o.')"
            class="block max-h-[80vh] w-full object-contain"
          />

          <!-- X -->
          <button
            class="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition hover:bg-black/70"
            @click="closeLightbox"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <!-- Left arrow -->
          <button
            v-if="lightboxPhotos.length > 1"
            class="absolute left-3 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition hover:bg-black/70"
            @click="lightboxPrev"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <!-- Right arrow -->
          <button
            v-if="lightboxPhotos.length > 1"
            class="absolute right-3 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition hover:bg-black/70"
            @click="lightboxNext"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <!-- Progress segments -->
          <div v-if="lightboxPhotos.length > 1" class="absolute inset-x-0 bottom-3 flex justify-center gap-1.5 px-6">
            <button
              v-for="(_, i) in lightboxPhotos"
              :key="i"
              class="h-1 flex-1 rounded-full transition-all duration-300"
              :class="i === lightboxIndex ? 'bg-white' : 'bg-white/35'"
              @click.stop="lightboxIndex = i"
            />
          </div>
        </div>

        <p
          v-if="lightboxPhotos[lightboxIndex].caption"
          class="mt-3 text-center text-sm italic text-white/70"
        >{{ lightboxPhotos[lightboxIndex].caption }}</p>
      </div>
    </div>
  </Transition>
  </Teleport>

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
        v-for="(item, idx) in pagedResults"
        :key="item.restaurant.id"
        class="overflow-hidden rounded-[1.75rem] border border-orange-950/10 bg-white/72 p-4 shadow-[0_18px_34px_rgba(28,25,23,0.06)]"
      >
        <div class="grid gap-4 sm:grid-cols-[12rem_minmax(0,1fr)]">

          <!-- Carousel -->
          <div class="relative h-40 overflow-hidden rounded-[1.5rem] bg-stone-100">
            <img
              v-if="photosFor(item.restaurant).length > 0"
              :src="photosFor(item.restaurant)[getPhotoIndex(item.restaurant.id)].url"
              :alt="item.restaurant.name"
              class="h-full w-full cursor-pointer object-cover"
              style="background: linear-gradient(135deg, rgba(251,146,60,0.3), rgba(124,45,18,0.22)), linear-gradient(135deg, #fcd9b6, #f5c88d);"
              @click="openLightbox(photosFor(item.restaurant), getPhotoIndex(item.restaurant.id))"
            />
            <div v-else class="restaurant-image flex h-full items-end p-4 text-white">
              <p class="text-base font-semibold">{{ item.restaurant.name }}</p>
            </div>

            <div
              v-if="photosFor(item.restaurant)[getPhotoIndex(item.restaurant.id)]?.caption"
              class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/65 to-transparent px-3 pb-2 pt-6"
            >
              <p class="truncate text-xs italic text-white/90">
                {{ photosFor(item.restaurant)[getPhotoIndex(item.restaurant.id)].caption }}
              </p>
            </div>

            <template v-if="photosFor(item.restaurant).length > 1">
              <button
                class="absolute left-1.5 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-black/30 text-white backdrop-blur-sm transition hover:bg-black/50"
                @click.stop="setPhotoIndex(item.restaurant.id, (getPhotoIndex(item.restaurant.id) - 1 + photosFor(item.restaurant).length) % photosFor(item.restaurant).length)"
              >
                <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <button
                class="absolute right-1.5 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-black/30 text-white backdrop-blur-sm transition hover:bg-black/50"
                @click.stop="setPhotoIndex(item.restaurant.id, (getPhotoIndex(item.restaurant.id) + 1) % photosFor(item.restaurant).length)"
              >
                <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <div class="absolute bottom-2 left-1/2 flex -translate-x-1/2 gap-1">
                <button
                  v-for="(_, i) in photosFor(item.restaurant)"
                  :key="i"
                  :class="i === getPhotoIndex(item.restaurant.id) ? 'w-3 bg-white' : 'w-1.5 bg-white/50'"
                  class="h-1 rounded-full transition-all duration-200"
                  @click.stop="setPhotoIndex(item.restaurant.id, i)"
                />
              </div>
            </template>
          </div>

          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-orange-700">#{{ (currentPage - 1) * PAGE_SIZE + idx + 1 }}</p>
              <p class="mt-2 text-2xl font-semibold text-stone-900">{{ item.restaurant.name }}</p>
              <div class="mt-2 space-y-1.5">
                <p v-if="item.restaurant.short_address || item.restaurant.address" class="flex items-start gap-1.5 text-sm text-stone-600">
                  <svg class="mt-0.5 h-3.5 w-3.5 shrink-0 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {{ item.restaurant.short_address ?? item.restaurant.address }}
                </p>
                <a
                  v-if="item.restaurant.phone"
                  :href="`tel:${item.restaurant.phone}`"
                  class="flex items-center gap-1.5 text-sm text-stone-600 transition-colors hover:text-orange-700"
                >
                  <svg class="h-3.5 w-3.5 shrink-0 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                  {{ item.restaurant.phone }}
                </a>
                <a
                  v-if="item.restaurant.yelp_url"
                  :href="item.restaurant.yelp_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center gap-1.5 text-sm text-stone-600 transition-colors hover:text-orange-700"
                >
                  <svg class="h-3.5 w-3.5 shrink-0 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  View on Yelp
                </a>
              </div>
              <div class="mt-3 flex flex-wrap gap-2">
                <span v-if="item.restaurant.price" class="metric-chip">
                  {{ formatRestaurantPrice(item.restaurant.price) }}
                </span>
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
      <!-- Pagination -->
      <div v-if="totalPages > 1" class="mt-6 flex items-center justify-center gap-1">
        <button
          class="flex h-9 w-9 items-center justify-center rounded-full bg-white/80 text-stone-500 transition hover:bg-white disabled:opacity-30"
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <template v-for="p in pageNumbers" :key="p">
          <span v-if="p === '…'" class="w-7 text-center text-sm text-stone-400">…</span>
          <button
            v-else
            class="h-9 w-9 rounded-full text-sm font-semibold transition"
            :class="p === currentPage
              ? 'bg-orange-600 text-white shadow'
              : 'bg-white/80 text-stone-700 hover:bg-white'"
            @click="currentPage = (p as number)"
          >{{ p }}</button>
        </template>

        <button
          class="flex h-9 w-9 items-center justify-center rounded-full bg-white/80 text-stone-500 transition hover:bg-white disabled:opacity-30"
          :disabled="currentPage === totalPages"
          @click="currentPage++"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

    <p v-else class="soft-alert mt-4 bg-stone-100 text-stone-700">
      No results yet. Votes will appear after participants start swiping.
    </p>
  </section>
</template>

<style scoped>
.lightbox-enter-active,
.lightbox-leave-active {
  transition: opacity 0.2s ease;
}
.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}
</style>
