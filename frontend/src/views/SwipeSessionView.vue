<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

import { getPopularDishes, getReviews } from "../lib/api";
import { formatRestaurantPrice } from "../lib/restaurant";
import { useSessionStore } from "../stores/session";
import type { PopularDishItem, ReviewItem } from "../types";

const store = useSessionStore();
let socket: WebSocket | null = null;

const photoIndex = ref(0);
const showHours = ref(false);

const lightboxOpen = ref(false);
const lightboxIndex = ref(0);
const lightboxDirection = ref<'next' | 'prev'>('next');
const carouselDirection = ref<'next' | 'prev'>('next');

const dishesOpen = ref(false);
const dishesLoading = ref(false);
const dishItems = ref<PopularDishItem[]>([]);

const dishLightboxOpen = ref(false);
const dishLightboxIndex = ref(0);
const dishLightboxDirection = ref<'next' | 'prev'>('next');
const dishPhotos = computed(() => dishItems.value.filter(d => d.photo_url));

const reviewsOpen = ref(false);
const reviewsLoading = ref(false);
const reviewItems = ref<ReviewItem[]>([]);
const reviewExpandedMap = ref<Record<number, boolean>>({});

function openLightbox(index: number) {
  lightboxIndex.value = index;
  lightboxOpen.value = true;
}

function closeLightbox() {
  lightboxOpen.value = false;
}

function lightboxPrev() {
  lightboxDirection.value = 'prev';
  lightboxIndex.value = (lightboxIndex.value - 1 + currentPhotos.value.length) % currentPhotos.value.length;
}

function lightboxNext() {
  lightboxDirection.value = 'next';
  lightboxIndex.value = (lightboxIndex.value + 1) % currentPhotos.value.length;
}

function lightboxGoTo(i: number) {
  lightboxDirection.value = i > lightboxIndex.value ? 'next' : 'prev';
  lightboxIndex.value = i;
}

function carouselPrev() {
  carouselDirection.value = 'prev';
  photoIndex.value = (photoIndex.value - 1 + currentPhotos.value.length) % currentPhotos.value.length;
}

function carouselNext() {
  carouselDirection.value = 'next';
  photoIndex.value = (photoIndex.value + 1) % currentPhotos.value.length;
}

function carouselGoTo(i: number) {
  carouselDirection.value = i > photoIndex.value ? 'next' : 'prev';
  photoIndex.value = i;
}

async function toggleReviews() {
  if (reviewsOpen.value) {
    reviewsOpen.value = false;
    return;
  }
  reviewsOpen.value = true;
  if (reviewItems.value.length > 0) return;
  reviewsLoading.value = true;
  try {
    const result = await getReviews(store.session!.room_code, store.currentRestaurant!.id);
    reviewItems.value = result.reviews;
  } catch {
    // silent — empty state handles it
  } finally {
    reviewsLoading.value = false;
  }
}

function openDishLightbox(dish: PopularDishItem) {
  const idx = dishPhotos.value.findIndex(d => d.photo_url === dish.photo_url);
  dishLightboxIndex.value = idx >= 0 ? idx : 0;
  dishLightboxDirection.value = 'next';
  dishLightboxOpen.value = true;
}

function closeDishLightbox() {
  dishLightboxOpen.value = false;
}

function dishLightboxPrev() {
  dishLightboxDirection.value = 'prev';
  dishLightboxIndex.value = (dishLightboxIndex.value - 1 + dishPhotos.value.length) % dishPhotos.value.length;
}

function dishLightboxNext() {
  dishLightboxDirection.value = 'next';
  dishLightboxIndex.value = (dishLightboxIndex.value + 1) % dishPhotos.value.length;
}

function dishLightboxGoTo(i: number) {
  dishLightboxDirection.value = i > dishLightboxIndex.value ? 'next' : 'prev';
  dishLightboxIndex.value = i;
}

async function openDishesModal() {
  dishesOpen.value = true;
  if (dishItems.value.length > 0) return;
  dishesLoading.value = true;
  try {
    const result = await getPopularDishes(store.session!.room_code, store.currentRestaurant!.id);
    dishItems.value = result.popular_dishes;
  } catch {
    // silent — empty state handles it
  } finally {
    dishesLoading.value = false;
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (dishLightboxOpen.value) {
    if (e.key === "Escape") closeDishLightbox();
    else if (e.key === "ArrowLeft") dishLightboxPrev();
    else if (e.key === "ArrowRight") dishLightboxNext();
  } else if (lightboxOpen.value) {
    if (e.key === "Escape") closeLightbox();
    else if (e.key === "ArrowLeft") lightboxPrev();
    else if (e.key === "ArrowRight") lightboxNext();
  } else if (dishesOpen.value && e.key === "Escape") {
    dishesOpen.value = false;
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

let dishLightboxTouchStartX = 0;

function dishLightboxTouchStart(e: TouchEvent) {
  dishLightboxTouchStartX = e.touches[0].clientX;
}

function dishLightboxTouchEnd(e: TouchEvent) {
  const delta = e.changedTouches[0].clientX - dishLightboxTouchStartX;
  if (Math.abs(delta) < 50) return;
  if (delta < 0) dishLightboxNext();
  else dishLightboxPrev();
}

let carouselTouchStartX = 0;

function carouselTouchStart(e: TouchEvent) {
  carouselTouchStartX = e.touches[0].clientX;
}

function carouselTouchEnd(e: TouchEvent) {
  const delta = e.changedTouches[0].clientX - carouselTouchStartX;
  if (Math.abs(delta) < 50) return;
  if (delta < 0) carouselNext();
  else carouselPrev();
}

const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const todayDayName = DAY_NAMES[new Date().getDay()];

const currentPhotos = computed(() => {
  const r = store.currentRestaurant;
  if (!r) return [];
  if (r.photos.length > 0) return r.photos;
  if (r.image_url) return [{ url: r.image_url, caption: null }];
  return [];
});

const todayHours = computed(() =>
  store.currentRestaurant?.hours?.find((h) => h.day === todayDayName)?.hours ?? null,
);

watch(() => store.currentRestaurant?.id, () => {
  photoIndex.value = 0;
  showHours.value = false;
  dishesOpen.value = false;
  dishItems.value = [];
  dishLightboxOpen.value = false;
  reviewsOpen.value = false;
  reviewItems.value = [];
  reviewExpandedMap.value = {};
  if (lightboxOpen.value) closeLightbox();
});

const celebrating = ref(false);
const celebrationName = ref("");
const celebrationImage = ref<string | null>(null);
let celebrationTimer: ReturnType<typeof setTimeout> | null = null;

function triggerCelebration(name: string, imageUrl: string | null) {
  if (celebrating.value) return;
  if (lightboxOpen.value) closeLightbox();
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
        user_name?: string;
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
      } else if (message.event === "participant_removed" && message.user_name === store.currentUser) {
        store.kickNotification = "You were removed from the session by the host.";
        store.resetState();
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
  window.addEventListener("keydown", handleKeydown);
  await store.loadNextRestaurant();
  if (store.session) {
    connectSocket(store.session.room_code);
  }
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
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

  <!-- Photo lightbox — teleported to body to escape hero-panel's backdrop-filter containing block -->
  <Teleport to="body">
  <Transition name="lightbox">
    <div
      v-if="lightboxOpen"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-md"
      @click.self="closeLightbox"
    >
      <div class="relative mx-4 w-full max-w-3xl">
        <!-- Image with all controls overlaid on top -->
        <div
          class="relative overflow-hidden rounded-2xl bg-black shadow-2xl"
          @touchstart.passive="lightboxTouchStart"
          @touchend="lightboxTouchEnd"
        >
          <div class="grid overflow-hidden">
            <Transition :name="lightboxDirection === 'next' ? 'lb-slide-left' : 'lb-slide-right'">
              <img
                :key="lightboxIndex"
                :src="currentPhotos[lightboxIndex].url.replace('/l.', '/o.')"
                :alt="store.currentRestaurant?.name"
                class="block max-h-[80vh] w-full object-contain"
              />
            </Transition>
          </div>

          <!-- X button — top right of image -->
          <button
            class="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition hover:bg-black/70"
            @click="closeLightbox"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <!-- Left arrow — overlaid on image -->
          <button
            v-if="currentPhotos.length > 1"
            class="absolute left-3 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition hover:bg-black/70"
            @click="lightboxPrev"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <!-- Right arrow — overlaid on image -->
          <button
            v-if="currentPhotos.length > 1"
            class="absolute right-3 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition hover:bg-black/70"
            @click="lightboxNext"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <!-- Progress segments — overlaid at bottom of image -->
          <div v-if="currentPhotos.length > 1" class="absolute inset-x-0 bottom-3 flex justify-center gap-1.5 px-6">
            <button
              v-for="(_, i) in currentPhotos"
              :key="i"
              class="h-1 flex-1 rounded-full transition-all duration-300"
              :class="i === lightboxIndex ? 'bg-white' : 'bg-white/35'"
              @click.stop="lightboxGoTo(i)"
            />
          </div>
        </div>

        <!-- Caption sits below the image box -->
        <p
          v-if="currentPhotos[lightboxIndex].caption"
          class="mt-3 text-center text-sm italic text-white/70"
        >{{ currentPhotos[lightboxIndex].caption }}</p>
      </div>
    </div>
  </Transition>
  </Teleport>

  <!-- Popular dishes modal -->
  <Teleport to="body">
  <Transition name="dishes-modal">
    <div
      v-if="dishesOpen"
      class="fixed inset-0 z-[60] flex items-end justify-center sm:items-center sm:p-4"
    >
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="dishesOpen = false" />
      <div class="relative z-10 max-h-[85vh] w-full overflow-y-auto rounded-t-[2rem] bg-white shadow-2xl sm:max-w-md sm:rounded-[1.75rem]">
        <div class="sticky top-0 border-b border-stone-100 bg-white/95 px-6 pb-4 pt-5 backdrop-blur-sm">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-stone-800">Popular Dishes</h2>
              <p class="mt-0.5 text-xs text-stone-400">{{ store.currentRestaurant?.name }}</p>
            </div>
            <button
              class="flex h-8 w-8 items-center justify-center rounded-full bg-stone-100 text-stone-500 transition-colors hover:bg-stone-200"
              @click="dishesOpen = false"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <div class="px-6 pb-6 pt-4">
          <div v-if="dishesLoading" class="flex justify-center py-10">
            <div class="h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
          </div>
          <p v-else-if="dishItems.length === 0" class="py-8 text-center text-sm text-stone-400">
            No popular dishes found for this restaurant.
          </p>
          <div v-else class="grid grid-cols-2 gap-3">
            <div
              v-for="dish in dishItems"
              :key="dish.display_name"
              class="overflow-hidden rounded-xl border border-stone-100 bg-stone-50"
            >
              <img
                v-if="dish.photo_url"
                :src="dish.photo_url"
                :alt="dish.display_name"
                class="aspect-square w-full cursor-pointer object-cover"
                @click="openDishLightbox(dish)"
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

  <!-- Dish photo lightbox -->
  <Teleport to="body">
  <Transition name="lightbox">
    <div
      v-if="dishLightboxOpen"
      class="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-md"
      @click.self="closeDishLightbox"
      @touchstart.passive="dishLightboxTouchStart"
      @touchend="dishLightboxTouchEnd"
    >
      <div class="relative mx-4 w-full max-w-lg">
        <div class="relative overflow-hidden rounded-2xl bg-black shadow-2xl">
          <div class="grid overflow-hidden">
            <Transition :name="dishLightboxDirection === 'next' ? 'lb-slide-left' : 'lb-slide-right'">
              <img
                :key="dishLightboxIndex"
                :src="dishPhotos[dishLightboxIndex].photo_url!"
                :alt="dishPhotos[dishLightboxIndex].display_name"
                class="block max-h-[80vh] w-full object-contain"
              />
            </Transition>
          </div>
          <button
            class="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition hover:bg-black/70"
            @click="closeDishLightbox"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <button
            v-if="dishPhotos.length > 1"
            class="absolute left-3 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition hover:bg-black/70"
            @click="dishLightboxPrev"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            v-if="dishPhotos.length > 1"
            class="absolute right-3 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition hover:bg-black/70"
            @click="dishLightboxNext"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <div v-if="dishPhotos.length > 1" class="absolute inset-x-0 bottom-3 flex justify-center gap-1.5 px-6">
            <button
              v-for="(_, i) in dishPhotos"
              :key="i"
              class="h-1 flex-1 rounded-full transition-all duration-300"
              :class="i === dishLightboxIndex ? 'bg-white' : 'bg-white/35'"
              @click.stop="dishLightboxGoTo(i)"
            />
          </div>
        </div>
        <p class="mt-3 text-center text-sm font-medium text-white/80">{{ dishPhotos[dishLightboxIndex].display_name }}</p>
      </div>
    </div>
  </Transition>
  </Teleport>

  <section class="glass-card">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <h2 class="section-title text-stone-900">Swipe Deck</h2>
        <span class="status-pill">Room: {{ store.session?.room_code }}</span>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="app-button-secondary"
          :disabled="store.resultsLoading"
          @click="store.openResults"
        >
          {{ store.resultsLoading ? "Loading..." : "View Results" }}
        </button>
        <button class="app-button" @click="store.resetState()">
          Back to Home
        </button>
      </div>
    </div>

    <div v-if="store.currentRestaurant" class="mt-6 overflow-hidden rounded-[1.75rem] border border-orange-950/10 bg-white/70 p-4 shadow-[0_20px_40px_rgba(28,25,23,0.08)]">
      <div class="grid gap-4 sm:grid-cols-[14rem_minmax(0,1fr)]">

        <!-- Square photo carousel + popular dishes -->
        <div class="flex flex-col gap-2">
        <div
          class="relative aspect-square overflow-hidden rounded-[1.5rem] bg-stone-100"
          @touchstart.passive="carouselTouchStart"
          @touchend="carouselTouchEnd"
        >
          <Transition :name="carouselDirection === 'next' ? 'carousel-left' : 'carousel-right'">
            <img
              v-if="currentPhotos.length > 0"
              :key="photoIndex"
              :src="currentPhotos[photoIndex].url"
              :alt="store.currentRestaurant.name"
              class="h-full w-full cursor-pointer object-cover"
              style="background: linear-gradient(135deg, rgba(251,146,60,0.3), rgba(124,45,18,0.22)), linear-gradient(135deg, #fcd9b6, #f5c88d);"
              @click="openLightbox(photoIndex)"
            />
          </Transition>
          <div v-if="currentPhotos.length === 0" class="restaurant-image flex h-full items-end p-5 text-white">
            <p class="text-xl font-semibold">{{ store.currentRestaurant.name }}</p>
          </div>

          <div
            v-if="currentPhotos[photoIndex]?.caption"
            class="absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-black/65 to-transparent px-4 pb-7 pt-8"
          >
            <p class="text-xs italic text-white/90">{{ currentPhotos[photoIndex].caption }}</p>
          </div>

          <template v-if="currentPhotos.length > 1">
            <button
              class="absolute left-2 top-1/2 z-10 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-black/30 text-lg text-white backdrop-blur-sm transition hover:bg-black/50"
              @click.stop="carouselPrev"
            >‹</button>
            <button
              class="absolute right-2 top-1/2 z-10 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-black/30 text-lg text-white backdrop-blur-sm transition hover:bg-black/50"
              @click.stop="carouselNext"
            >›</button>
            <div class="absolute bottom-2.5 left-1/2 z-10 flex -translate-x-1/2 gap-1">
              <button
                v-for="(_, i) in currentPhotos"
                :key="i"
                :class="i === photoIndex ? 'w-4 bg-white' : 'w-1.5 bg-white/50'"
                class="h-1.5 rounded-full transition-all duration-200"
                @click.stop="carouselGoTo(i)"
              />
            </div>
          </template>
        </div>

        <!-- Popular dishes button -->
        <button
          class="metric-chip w-full cursor-pointer justify-center gap-1.5 hover:opacity-75 transition-opacity"
          @click="openDishesModal"
        >
          <svg class="h-3.5 w-3.5 text-stone-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          Popular Dishes
        </button>
        </div>

        <!-- Info + vote column -->
        <div class="flex flex-col gap-3">
          <div class="min-w-0">
            <p class="text-2xl font-semibold text-stone-900">{{ store.currentRestaurant.name }}</p>

            <!-- Address / phone / Yelp -->
            <div class="mt-2 space-y-2">
              <p v-if="store.currentRestaurant.short_address || store.currentRestaurant.address" class="flex items-start gap-1.5 text-sm text-stone-600">
                <svg class="mt-0.5 h-3.5 w-3.5 shrink-0 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {{ store.currentRestaurant.short_address ?? store.currentRestaurant.address }}
              </p>
              <a
                v-if="store.currentRestaurant.phone"
                :href="`tel:${store.currentRestaurant.phone}`"
                class="flex w-fit items-center gap-1.5 text-sm text-stone-600 hover:text-orange-700 transition-colors"
              >
                <svg class="h-3.5 w-3.5 shrink-0 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                {{ store.currentRestaurant.phone }}
              </a>
              <a
                v-if="store.currentRestaurant.yelp_url"
                :href="store.currentRestaurant.yelp_url"
                target="_blank"
                rel="noopener noreferrer"
                class="flex w-fit items-center gap-1.5 text-sm text-stone-600 hover:text-orange-700 transition-colors"
              >
                <svg class="h-3.5 w-3.5 shrink-0 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                View on Yelp
              </a>
            </div>

            <!-- Hours -->
            <div v-if="store.currentRestaurant.hours?.length" class="mt-3">
              <button
                class="flex w-full items-center gap-1.5 text-left"
                @click="showHours = !showHours"
              >
                <svg class="h-3.5 w-3.5 shrink-0 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span class="text-sm text-stone-600">
                  <span v-if="todayHours">Today: {{ todayHours }}</span>
                  <span v-else class="text-stone-400">See hours</span>
                </span>
                <svg
                  class="ml-auto h-3.5 w-3.5 shrink-0 text-stone-400 transition-transform duration-200"
                  :class="showHours ? 'rotate-180' : ''"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <Transition name="hours-expand">
                <div v-if="showHours" class="mt-2 space-y-1 rounded-xl bg-stone-50/80 px-3 py-2.5">
                  <div
                    v-for="item in store.currentRestaurant.hours"
                    :key="item.day"
                    class="flex justify-between text-xs"
                    :class="item.day === todayDayName ? 'font-semibold text-stone-900' : 'text-stone-500'"
                  >
                    <span>{{ item.day }}</span>
                    <span>{{ item.hours }}</span>
                  </div>
                </div>
              </Transition>
            </div>
          </div>

          <!-- Category + metric chips -->
          <div class="flex flex-wrap gap-2">
            <span
              v-for="cat in store.currentRestaurant.categories.slice(0, 3)"
              :key="cat"
              class="inline-flex items-center rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-700"
            >{{ cat }}</span>
            <span v-if="store.currentRestaurant.price" class="metric-chip">
              {{ formatRestaurantPrice(store.currentRestaurant.price) }}
            </span>
            <span v-if="store.currentRestaurant.rating" class="metric-chip">{{ store.currentRestaurant.rating }} stars</span>
            <button v-if="store.currentRestaurant.review_count" class="metric-chip cursor-pointer hover:opacity-75 transition-opacity inline-flex items-center gap-1" @click="toggleReviews">
              {{ store.currentRestaurant.review_count }} reviews
              <svg class="h-3 w-3 transition-transform" :class="reviewsOpen ? 'rotate-180' : ''" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>

          <!-- Inline reviews panel -->
          <Transition name="hours-expand">
            <div v-if="reviewsOpen" class="space-y-2 rounded-xl bg-stone-50/80 px-3 py-2.5">
              <div v-if="reviewsLoading" class="flex justify-center py-3">
                <div class="h-5 w-5 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
              </div>
              <p v-else-if="reviewItems.length === 0" class="text-center text-xs text-stone-400 py-2">No reviews found.</p>
              <div v-else v-for="(review, idx) in reviewItems" :key="review.author_name + review.created_at" class="space-y-1">
                <div class="flex items-center gap-2">
                  <img v-if="review.author_photo_url" :src="review.author_photo_url" :alt="review.author_name" class="h-6 w-6 rounded-full object-cover shrink-0" />
                  <div v-else class="h-6 w-6 rounded-full bg-stone-200 flex items-center justify-center shrink-0">
                    <span class="text-[10px] font-semibold text-stone-500">{{ review.author_name.charAt(0) }}</span>
                  </div>
                  <div class="min-w-0">
                    <span class="text-xs font-semibold text-stone-700">{{ review.author_name }}</span>
                    <span v-if="review.author_location" class="text-xs text-stone-400"> · {{ review.author_location }}</span>
                  </div>
                  <div class="ml-auto flex items-center gap-1 shrink-0">
                    <span class="text-xs text-orange-500">{{ '★'.repeat(review.rating) }}{{ '☆'.repeat(5 - review.rating) }}</span>
                  </div>
                </div>
                <p class="text-xs text-stone-600 leading-relaxed" :class="reviewExpandedMap[idx] ? '' : 'line-clamp-3'">{{ review.text }}</p>
                <button v-if="review.text.length > 200 && !reviewExpandedMap[idx]" class="text-xs text-orange-500 hover:text-orange-600 transition-colors" @click="reviewExpandedMap[idx] = true">see more</button>
                <button v-else-if="reviewExpandedMap[idx]" class="text-xs text-orange-500 hover:text-orange-600 transition-colors" @click="reviewExpandedMap[idx] = false">see less</button>
                <div v-if="idx < reviewItems.length - 1" class="border-t border-stone-200 pt-2" />
              </div>
            </div>
          </Transition>

          <!-- Vote progress -->
          <div v-if="store.voteProgress" class="rounded-2xl bg-stone-50/80 px-3 py-2.5">
            <div class="mb-1.5 flex items-center justify-between">
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

          <!-- Vote buttons -->
          <div class="grid grid-cols-2 gap-3">
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

.hours-expand-enter-active,
.hours-expand-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.hours-expand-enter-from,
.hours-expand-leave-to {
  opacity: 0;
  transform: translateY(-4px);
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

.dishes-modal-enter-active,
.dishes-modal-leave-active {
  transition: opacity 0.2s ease;
}
.dishes-modal-enter-from,
.dishes-modal-leave-to {
  opacity: 0;
}

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
