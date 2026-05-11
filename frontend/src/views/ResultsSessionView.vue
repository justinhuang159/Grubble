<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import { getPopularDishes } from "../lib/api";
import { formatRestaurantPrice } from "../lib/restaurant";
import { useSessionStore } from "../stores/session";
import type { PopularDishItem, RestaurantCard } from "../types";

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
const carouselDirections = ref<Record<number, 'next' | 'prev'>>({});

function getPhotoIndex(id: number): number {
  return photoIndexes.value[id] ?? 0;
}

function getCarouselDirection(id: number): 'next' | 'prev' {
  return carouselDirections.value[id] ?? 'next';
}

function setPhotoIndex(id: number, i: number) {
  photoIndexes.value[id] = i;
}

function resultCarouselPrev(id: number, photos: { url: string; caption: string | null }[]) {
  carouselDirections.value[id] = 'prev';
  setPhotoIndex(id, (getPhotoIndex(id) - 1 + photos.length) % photos.length);
}

function resultCarouselNext(id: number, photos: { url: string; caption: string | null }[]) {
  carouselDirections.value[id] = 'next';
  setPhotoIndex(id, (getPhotoIndex(id) + 1) % photos.length);
}

function resultCarouselGoTo(id: number, i: number) {
  carouselDirections.value[id] = i > getPhotoIndex(id) ? 'next' : 'prev';
  setPhotoIndex(id, i);
}

function photosFor(r: RestaurantCard) {
  if (r.photos.length > 0) return r.photos;
  if (r.image_url) return [{ url: r.image_url, caption: null }];
  return [];
}

// Popular dishes
const activeDishesId = ref<number | null>(null);
const dishesLoadingMap = ref<Record<number, boolean>>({});
const dishItemsMap = ref<Record<number, PopularDishItem[]>>({});

const activeDishes = computed(() =>
  activeDishesId.value !== null ? (dishItemsMap.value[activeDishesId.value] ?? []) : [],
);
const activeDishesLoading = computed(() =>
  activeDishesId.value !== null ? (dishesLoadingMap.value[activeDishesId.value] ?? false) : false,
);
const activeDishesName = computed(() => {
  if (activeDishesId.value === null) return '';
  return rankedResults.value.find((r) => r.restaurant.id === activeDishesId.value)?.restaurant.name ?? '';
});

async function openDishesModal(restaurantId: number) {
  activeDishesId.value = restaurantId;
  if (dishItemsMap.value[restaurantId]?.length) return;
  dishesLoadingMap.value[restaurantId] = true;
  try {
    const result = await getPopularDishes(store.session!.room_code, restaurantId);
    dishItemsMap.value[restaurantId] = result.popular_dishes;
  } catch {
    dishItemsMap.value[restaurantId] = [];
  } finally {
    dishesLoadingMap.value[restaurantId] = false;
  }
}

function closeDishesModal() {
  activeDishesId.value = null;
}

// Lightbox
const lightboxOpen = ref(false);
const lightboxPhotos = ref<{ url: string; caption: string | null }[]>([]);
const lightboxIndex = ref(0);
const lightboxDirection = ref<'next' | 'prev'>('next');

function openLightbox(photos: { url: string; caption: string | null }[], index: number) {
  lightboxPhotos.value = photos;
  lightboxIndex.value = index;
  lightboxOpen.value = true;
}

function closeLightbox() {
  lightboxOpen.value = false;
}

function lightboxPrev() {
  lightboxDirection.value = 'prev';
  lightboxIndex.value = (lightboxIndex.value - 1 + lightboxPhotos.value.length) % lightboxPhotos.value.length;
}

function lightboxNext() {
  lightboxDirection.value = 'next';
  lightboxIndex.value = (lightboxIndex.value + 1) % lightboxPhotos.value.length;
}

function lightboxGoTo(i: number) {
  lightboxDirection.value = i > lightboxIndex.value ? 'next' : 'prev';
  lightboxIndex.value = i;
}

function handleKeydown(e: KeyboardEvent) {
  if (lightboxOpen.value) {
    if (e.key === "Escape") closeLightbox();
    else if (e.key === "ArrowLeft") lightboxPrev();
    else if (e.key === "ArrowRight") lightboxNext();
  } else if (activeDishesId.value !== null && e.key === "Escape") {
    closeDishesModal();
  }
}

let lightboxTouchStartX = 0;

function lightboxTouchStart(e: TouchEvent) {
  lightboxTouchStartX = e.touches[0].clientX;
}

function lightboxTouchEnd(e: TouchEvent) {
  const delta = e.changedTouches[0].clientX - lightboxTouchStartX;
  if (Math.abs(delta) < 50) return;
  if (delta < 0) lightboxNext();
  else lightboxPrev();
}

let carouselTouchStartX = 0;

function carouselTouchStart(e: TouchEvent) {
  carouselTouchStartX = e.touches[0].clientX;
}

function carouselTouchEnd(e: TouchEvent, id: number, photos: { url: string; caption: string | null }[]) {
  const delta = e.changedTouches[0].clientX - carouselTouchStartX;
  if (Math.abs(delta) < 50) return;
  if (delta < 0) resultCarouselNext(id, photos);
  else resultCarouselPrev(id, photos);
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
        <div
          class="relative overflow-hidden rounded-2xl bg-black shadow-2xl"
          @touchstart.passive="lightboxTouchStart"
          @touchend="lightboxTouchEnd"
        >
          <div class="grid overflow-hidden">
            <Transition :name="lightboxDirection === 'next' ? 'lb-slide-left' : 'lb-slide-right'">
              <img
                :key="lightboxIndex"
                :src="lightboxPhotos[lightboxIndex].url.replace('/l.', '/o.')"
                class="block max-h-[80vh] w-full object-contain"
              />
            </Transition>
          </div>

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
              @click.stop="lightboxGoTo(i)"
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

  <!-- Popular dishes modal -->
  <Teleport to="body">
  <Transition name="dishes-modal">
    <div
      v-if="activeDishesId !== null"
      class="fixed inset-0 z-[60] flex items-end justify-center sm:items-center sm:p-4"
    >
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeDishesModal" />
      <div class="relative z-10 max-h-[85vh] w-full overflow-y-auto rounded-t-[2rem] bg-white shadow-2xl sm:max-w-md sm:rounded-[1.75rem]">
        <div class="sticky top-0 border-b border-stone-100 bg-white/95 px-6 pb-4 pt-5 backdrop-blur-sm">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-stone-800">Popular Dishes</h2>
              <p class="mt-0.5 text-xs text-stone-400">{{ activeDishesName }}</p>
            </div>
            <button
              class="flex h-8 w-8 items-center justify-center rounded-full bg-stone-100 text-stone-500 transition-colors hover:bg-stone-200"
              @click="closeDishesModal"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <div class="px-6 pb-6 pt-4">
          <div v-if="activeDishesLoading" class="flex justify-center py-10">
            <div class="h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
          </div>
          <p v-else-if="activeDishes.length === 0" class="py-8 text-center text-sm text-stone-400">
            No popular dishes found for this restaurant.
          </p>
          <div v-else class="grid grid-cols-2 gap-3">
            <div
              v-for="dish in activeDishes"
              :key="dish.display_name"
              class="overflow-hidden rounded-xl border border-stone-100 bg-stone-50"
            >
              <img
                v-if="dish.photo_url"
                :src="dish.photo_url"
                :alt="dish.display_name"
                class="aspect-square w-full object-cover"
              />
              <div v-else class="flex aspect-square items-center justify-center bg-stone-100">
                <svg class="h-8 w-8 text-stone-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div class="p-2.5">
                <p class="text-sm font-medium leading-tight text-stone-800">{{ dish.display_name }}</p>
                <p class="mt-0.5 text-xs text-stone-400">{{ dish.review_count }} reviews</p>
              </div>
            </div>
          </div>
        </div>
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
          <div
            class="relative h-40 overflow-hidden rounded-[1.5rem] bg-stone-100"
            @touchstart.passive="carouselTouchStart"
            @touchend="carouselTouchEnd($event, item.restaurant.id, photosFor(item.restaurant))"
          >
            <Transition :name="getCarouselDirection(item.restaurant.id) === 'next' ? 'carousel-left' : 'carousel-right'">
              <img
                v-if="photosFor(item.restaurant).length > 0"
                :key="getPhotoIndex(item.restaurant.id)"
                :src="photosFor(item.restaurant)[getPhotoIndex(item.restaurant.id)].url"
                :alt="item.restaurant.name"
                class="h-full w-full cursor-pointer object-cover"
                style="background: linear-gradient(135deg, rgba(251,146,60,0.3), rgba(124,45,18,0.22)), linear-gradient(135deg, #fcd9b6, #f5c88d);"
                @click="openLightbox(photosFor(item.restaurant), getPhotoIndex(item.restaurant.id))"
              />
            </Transition>
            <div v-if="photosFor(item.restaurant).length === 0" class="restaurant-image flex h-full items-end p-4 text-white">
              <p class="text-base font-semibold">{{ item.restaurant.name }}</p>
            </div>

            <div
              v-if="photosFor(item.restaurant)[getPhotoIndex(item.restaurant.id)]?.caption"
              class="absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-black/65 to-transparent px-3 pb-2 pt-6"
            >
              <p class="truncate text-xs italic text-white/90">
                {{ photosFor(item.restaurant)[getPhotoIndex(item.restaurant.id)].caption }}
              </p>
            </div>

            <template v-if="photosFor(item.restaurant).length > 1">
              <button
                class="absolute left-1.5 top-1/2 z-10 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-black/30 text-white backdrop-blur-sm transition hover:bg-black/50"
                @click.stop="resultCarouselPrev(item.restaurant.id, photosFor(item.restaurant))"
              >
                <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <button
                class="absolute right-1.5 top-1/2 z-10 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-black/30 text-white backdrop-blur-sm transition hover:bg-black/50"
                @click.stop="resultCarouselNext(item.restaurant.id, photosFor(item.restaurant))"
              >
                <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <div class="absolute bottom-2 left-1/2 z-10 flex -translate-x-1/2 gap-1">
                <button
                  v-for="(_, i) in photosFor(item.restaurant)"
                  :key="i"
                  :class="i === getPhotoIndex(item.restaurant.id) ? 'w-3 bg-white' : 'w-1.5 bg-white/50'"
                  class="h-1 rounded-full transition-all duration-200"
                  @click.stop="resultCarouselGoTo(item.restaurant.id, i)"
                />
              </div>
            </template>
          </div>

          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
            <div class="min-w-0">
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-orange-700">#{{ (currentPage - 1) * PAGE_SIZE + idx + 1 }}</p>
              <p class="mt-2 text-2xl font-semibold text-stone-900">{{ item.restaurant.name }}</p>
              <div class="mt-2 space-y-2">
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
              <button
                class="mt-3 inline-flex items-center gap-1.5 rounded-full border border-stone-200 bg-white px-3 py-1 text-sm font-medium text-stone-600 transition-colors hover:bg-stone-50"
                @click="openDishesModal(item.restaurant.id)"
              >
                <svg class="h-3.5 w-3.5 text-stone-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                Popular Dishes
              </button>
            </div>
            <div class="shrink-0 rounded-2xl bg-emerald-50 px-4 py-3 text-right">
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
.dishes-modal-enter-active,
.dishes-modal-leave-active {
  transition: opacity 0.2s ease;
}
.dishes-modal-enter-from,
.dishes-modal-leave-to {
  opacity: 0;
}

.lightbox-enter-active,
.lightbox-leave-active {
  transition: opacity 0.2s ease;
}
.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}

/* Carousel slide — absolute so both images overlap inside the fixed-height container */
.carousel-left-enter-active,
.carousel-left-leave-active,
.carousel-right-enter-active,
.carousel-right-leave-active {
  transition: transform 0.3s ease;
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.carousel-left-enter-from  { transform: translateX(100%); }
.carousel-left-leave-to    { transform: translateX(-100%); }
.carousel-right-enter-from { transform: translateX(-100%); }
.carousel-right-leave-to   { transform: translateX(100%); }

/* Lightbox slide — grid-area stacking so both images share the same cell */
.lb-slide-left-enter-active,
.lb-slide-left-leave-active,
.lb-slide-right-enter-active,
.lb-slide-right-leave-active {
  transition: transform 0.3s ease;
  grid-area: 1 / 1;
}
.lb-slide-left-enter-from  { transform: translateX(100%); }
.lb-slide-left-leave-to    { transform: translateX(-100%); }
.lb-slide-right-enter-from { transform: translateX(-100%); }
.lb-slide-right-leave-to   { transform: translateX(100%); }
</style>
