<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

import { formatRestaurantPrice } from "../lib/restaurant";
import { useSessionStore } from "../stores/session";

const store = useSessionStore();
let socket: WebSocket | null = null;

const photoIndex = ref(0);
const showHours = ref(false);

const lightboxOpen = ref(false);
const lightboxIndex = ref(0);

function openLightbox(index: number) {
  lightboxIndex.value = index;
  lightboxOpen.value = true;
}

function closeLightbox() {
  lightboxOpen.value = false;
}

function lightboxPrev() {
  lightboxIndex.value = (lightboxIndex.value - 1 + currentPhotos.value.length) % currentPhotos.value.length;
}

function lightboxNext() {
  lightboxIndex.value = (lightboxIndex.value + 1) % currentPhotos.value.length;
}

function handleKeydown(e: KeyboardEvent) {
  if (!lightboxOpen.value) return;
  if (e.key === "Escape") closeLightbox();
  else if (e.key === "ArrowLeft") lightboxPrev();
  else if (e.key === "ArrowRight") lightboxNext();
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

  <!-- Photo lightbox -->
  <Transition name="lightbox">
    <div
      v-if="lightboxOpen"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-md"
      @click.self="closeLightbox"
    >
      <div class="relative mx-4 w-full max-w-3xl">
        <!-- Image with all controls overlaid on top -->
        <div class="relative overflow-hidden rounded-2xl bg-black shadow-2xl">
          <img
            :src="currentPhotos[lightboxIndex].url.replace('/l.', '/o.')"
            :alt="store.currentRestaurant?.name"
            class="block max-h-[80vh] w-full object-contain"
          />

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
              @click.stop="lightboxIndex = i"
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

      <!-- Photo carousel -->
      <div class="relative h-56 overflow-hidden rounded-[1.5rem] bg-stone-100">
        <img
          v-if="currentPhotos.length > 0"
          :src="currentPhotos[photoIndex].url"
          :alt="store.currentRestaurant.name"
          class="h-full w-full cursor-pointer object-cover"
          style="background: linear-gradient(135deg, rgba(251,146,60,0.3), rgba(124,45,18,0.22)), linear-gradient(135deg, #fcd9b6, #f5c88d);"
          @click="openLightbox(photoIndex)"
        />
        <div v-else class="restaurant-image flex h-full items-end p-5 text-white">
          <p class="text-xl font-semibold">{{ store.currentRestaurant.name }}</p>
        </div>

        <div
          v-if="currentPhotos[photoIndex]?.caption"
          class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/65 to-transparent px-4 pb-3 pt-8"
        >
          <p class="text-xs italic text-white/90">{{ currentPhotos[photoIndex].caption }}</p>
        </div>

        <template v-if="currentPhotos.length > 1">
          <button
            class="absolute left-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-black/30 text-lg text-white backdrop-blur-sm transition hover:bg-black/50"
            @click.stop="photoIndex = (photoIndex - 1 + currentPhotos.length) % currentPhotos.length"
          >‹</button>
          <button
            class="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-black/30 text-lg text-white backdrop-blur-sm transition hover:bg-black/50"
            @click.stop="photoIndex = (photoIndex + 1) % currentPhotos.length"
          >›</button>
          <div class="absolute bottom-2.5 left-1/2 flex -translate-x-1/2 gap-1">
            <button
              v-for="(_, i) in currentPhotos"
              :key="i"
              :class="i === photoIndex ? 'w-4 bg-white' : 'w-1.5 bg-white/50'"
              class="h-1.5 rounded-full transition-all duration-200"
              @click.stop="photoIndex = i"
            />
          </div>
        </template>
      </div>

      <div class="mt-5 flex flex-wrap items-start justify-between gap-4">
        <div class="min-w-0 flex-1">
          <p class="text-2xl font-semibold text-stone-900">{{ store.currentRestaurant.name }}</p>

          <!-- Address / phone / Yelp -->
          <div class="mt-2 space-y-1.5">
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
              class="flex items-center gap-1.5 text-sm text-stone-600 hover:text-orange-700 transition-colors"
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
              class="flex items-center gap-1.5 text-sm text-stone-600 hover:text-orange-700 transition-colors"
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

        <div class="flex flex-wrap justify-end gap-2">
          <span
            v-for="cat in store.currentRestaurant.categories.slice(0, 3)"
            :key="cat"
            class="inline-flex items-center rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-700"
          >{{ cat }}</span>
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
</style>
