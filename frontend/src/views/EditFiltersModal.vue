<script setup lang="ts">
import { ref } from "vue";
import { useSessionStore } from "../stores/session";

const props = defineProps<{
  roomCode: string;
  initial: {
    location_text: string | null;
    cuisine: string | null;
    price: string | null;
    radius_meters: number | null;
  };
}>();

const emit = defineEmits<{ close: []; saved: [] }>();

const store = useSessionStore();

function metersToMiles(m: number | null): number {
  return m ? Math.round((m / 1609.34) * 10) / 10 : 5;
}

function parsePrice(price: string | null): number[] {
  if (!price) return [];
  return price.split(",").map(Number).filter((n) => n >= 1 && n <= 4);
}

const locationText = ref(props.initial.location_text ?? "");
const cuisine = ref(props.initial.cuisine ?? "");
const radiusMiles = ref(metersToMiles(props.initial.radius_meters));
const selectedPriceTiers = ref<number[]>(parsePrice(props.initial.price));

const loading = ref(false);
const error = ref("");

function toggleTier(tier: number) {
  const idx = selectedPriceTiers.value.indexOf(tier);
  if (idx >= 0) selectedPriceTiers.value.splice(idx, 1);
  else selectedPriceTiers.value.push(tier);
}

async function save() {
  error.value = "";
  loading.value = true;
  try {
    await store.updateFilters(props.roomCode, {
      location_text: locationText.value.trim() || null,
      cuisine: cuisine.value.trim() || null,
      price: selectedPriceTiers.value.length
        ? [...selectedPriceTiers.value].sort().join(",")
        : null,
      radius_meters: Math.round(radiusMiles.value * 1609.34),
    });
    emit("saved");
    emit("close");
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Could not save filters.";
  } finally {
    loading.value = false;
  }
}

function onBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) emit("close");
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") emit("close");
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      @click="onBackdropClick"
      @keydown="onKeydown"
    >
      <div class="glass-card w-full max-w-sm">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="section-title text-stone-900">Edit Filters</h2>
            <p class="section-copy">Adjust the session before it starts.</p>
          </div>
          <button
            class="mt-0.5 rounded-full p-1 text-stone-400 transition-colors hover:bg-stone-100 hover:text-stone-600"
            aria-label="Close"
            @click="emit('close')"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="mt-4 space-y-4">
          <div>
            <label class="field-label" for="ef-location">Location</label>
            <input
              id="ef-location"
              v-model="locationText"
              class="app-input"
              type="text"
              placeholder="Neighborhood, city, or full address"
              autocomplete="off"
            />
          </div>

          <div>
            <div class="flex items-baseline justify-between">
              <label class="field-label" for="ef-radius">Search Radius</label>
              <span class="text-xs font-medium text-stone-500">{{ radiusMiles }} mi</span>
            </div>
            <input
              id="ef-radius"
              v-model.number="radiusMiles"
              class="mt-1.5 w-full accent-orange-500"
              min="1"
              max="25"
              step="1"
              type="range"
            />
            <div class="mt-1 flex justify-between text-[0.65rem] text-stone-400">
              <span>1 mi</span>
              <span>25 mi</span>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="field-label" for="ef-cuisine">Cuisine</label>
              <input
                id="ef-cuisine"
                v-model="cuisine"
                class="app-input"
                placeholder="Sushi, burgers, tapas..."
              />
            </div>
            <div>
              <label class="field-label">Budget</label>
              <div class="mt-1.5 flex gap-2">
                <button
                  v-for="(label, i) in ['$', '$$', '$$$', '$$$$']"
                  :key="i"
                  type="button"
                  class="flex-1 rounded-full border py-1.5 text-sm font-medium transition-colors"
                  :class="selectedPriceTiers.includes(i + 1)
                    ? 'border-orange-400 bg-orange-50 text-orange-700'
                    : 'border-stone-200 bg-white text-stone-500 hover:border-stone-300 hover:text-stone-700'"
                  @click="toggleTier(i + 1)"
                >
                  {{ label }}
                </button>
              </div>
            </div>
          </div>

          <Transition name="error-banner">
            <div
              v-if="error"
              class="flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {{ error }}
            </div>
          </Transition>

          <div class="flex gap-2">
            <button class="app-button flex-1" :disabled="loading" @click="save">
              {{ loading ? "Saving..." : "Save" }}
            </button>
            <button
              class="flex-1 rounded-xl border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-600 transition-colors hover:border-stone-300 hover:text-stone-800"
              @click="emit('close')"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.error-banner-enter-active,
.error-banner-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.error-banner-enter-from,
.error-banner-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
