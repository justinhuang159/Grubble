<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";

import { useAuthStore } from "../stores/auth";
import { useSessionStore } from "../stores/session";
import { validateLocation } from "../lib/api";

interface NominatimResult {
  display_name: string;
  address?: {
    neighbourhood?: string;
    quarter?: string;
    borough?: string;
    suburb?: string;
    city?: string;
    town?: string;
    village?: string;
    state?: string;
    country?: string;
    country_code?: string;
  };
}

const emit = defineEmits<{
  created: [];
}>();

const auth = useAuthStore();
const store = useSessionStore();
const hostName = ref("");

onMounted(() => {
  if (!hostName.value && auth.displayName) hostName.value = auth.displayName;
});

watch(
  () => auth.displayName,
  (name) => { if (!hostName.value && name) hostName.value = name; }
);
const locationText = ref("");
const cuisine = ref("");
const selectedPriceTiers = ref<number[]>([]);
const radiusMiles = ref(5);
const submitted = ref(false);

const locationSuggestions = ref<NominatimResult[]>([]);
const showSuggestions = ref(false);
const highlightedIndex = ref(-1);
const locationValidation = ref<"idle" | "validating" | "valid" | "invalid">("idle");
const geoLoading = ref(false);
const geoError = ref("");
let nominatimTimer: ReturnType<typeof setTimeout> | null = null;
let validationTimer: ReturnType<typeof setTimeout> | null = null;

const hostNameInvalid = computed(() => submitted.value && !hostName.value.trim());
const locationInvalid = computed(() => submitted.value && !locationText.value.trim());
const hasErrors = computed(() => hostNameInvalid.value || locationInvalid.value);

function formatSuggestion(r: NominatimResult): string {
  const a = r.address;
  if (!a) return r.display_name;
  const region = a.state ?? a.country;
  const specific = a.neighbourhood ?? a.quarter;
  if (specific) {
    const mid = a.borough ?? a.suburb ?? a.city ?? a.town ?? a.village;
    return [specific, mid, region].filter(Boolean).join(", ");
  }
  const locality = a.borough ?? a.suburb ?? a.city ?? a.town ?? a.village;
  if (locality && region) return `${locality}, ${region}`;
  if (locality) return locality;
  return r.display_name.split(",").slice(0, 2).join(",").trim();
}

watch(locationText, (val) => {
  locationValidation.value = "idle";
  if (nominatimTimer) clearTimeout(nominatimTimer);
  if (!val || val.length < 3) {
    locationSuggestions.value = [];
    showSuggestions.value = false;
    return;
  }
  nominatimTimer = setTimeout(async () => {
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(val)}&format=json&limit=5&addressdetails=1`,
      );
      locationSuggestions.value = await res.json();
      showSuggestions.value = locationSuggestions.value.length > 0;
      highlightedIndex.value = -1;
    } catch {
      /* silent */
    }
  }, 350);
});

function selectSuggestion(r: NominatimResult) {
  locationText.value = formatSuggestion(r);
  showSuggestions.value = false;
  locationSuggestions.value = [];
  triggerValidation(locationText.value);
}

function triggerValidation(val: string) {
  if (!val) return;
  locationValidation.value = "validating";
  if (validationTimer) clearTimeout(validationTimer);
  validationTimer = setTimeout(async () => {
    try {
      const { valid } = await validateLocation(val);
      locationValidation.value = valid ? "valid" : "invalid";
    } catch {
      locationValidation.value = "idle";
    }
  }, 600);
}

async function useCurrentLocation() {
  if (!navigator.geolocation) {
    geoError.value = "Geolocation is not supported by your browser.";
    return;
  }
  geoLoading.value = true;
  geoError.value = "";
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      try {
        const { latitude: lat, longitude: lon } = pos.coords;
        const res = await fetch(
          `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json&zoom=10&addressdetails=1`,
        );
        const data: NominatimResult = await res.json();
        locationText.value = formatSuggestion(data);
        locationSuggestions.value = [];
        showSuggestions.value = false;
        triggerValidation(locationText.value);
      } catch {
        geoError.value = "Could not determine your location. Please type it manually.";
      } finally {
        geoLoading.value = false;
      }
    },
    () => {
      geoError.value = "Location access denied. Please type your location manually.";
      geoLoading.value = false;
    },
  );
}

function onLocationBlur() {
  setTimeout(() => { showSuggestions.value = false; }, 150);
  triggerValidation(locationText.value);
}

function onLocationKeydown(e: KeyboardEvent) {
  if (!showSuggestions.value) return;
  if (e.key === "ArrowDown") {
    e.preventDefault();
    highlightedIndex.value = Math.min(highlightedIndex.value + 1, locationSuggestions.value.length - 1);
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    highlightedIndex.value = Math.max(highlightedIndex.value - 1, -1);
  } else if (e.key === "Enter" && highlightedIndex.value >= 0) {
    e.preventDefault();
    selectSuggestion(locationSuggestions.value[highlightedIndex.value]);
  } else if (e.key === "Escape") {
    showSuggestions.value = false;
  }
}

async function submit() {
  submitted.value = true;
  if (hasErrors.value) return;
  await store.create({
    host_name: hostName.value,
    location_text: locationText.value,
    cuisine: cuisine.value || undefined,
    price: selectedPriceTiers.value.length ? [...selectedPriceTiers.value].sort().join(",") : undefined,
    radius_miles: radiusMiles.value || undefined,
  });
  emit("created");
}
</script>

<template>
  <section class="glass-card">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="section-title text-stone-900">Create a Table</h2>
        <p class="section-copy">Set the mood, location, and filters. We'll turn that into a room everyone can jump into fast.</p>
      </div>
      <span class="status-pill">Host Flow</span>
    </div>
    <form class="mt-4 space-y-4" @submit.prevent="submit">

      <Transition name="error-banner">
        <div
          v-if="hasErrors"
          class="flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          <svg class="h-4 w-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
          Please fill in all required fields before continuing.
        </div>
      </Transition>

      <div>
        <label class="field-label" for="host-name">Host Name <span class="text-orange-600">*</span></label>
        <input
          id="host-name"
          v-model="hostName"
          class="app-input"
          :class="hostNameInvalid ? 'border-red-400 bg-red-50/40 focus:border-red-500 focus:ring-red-200' : ''"
          placeholder="Who is leading tonight?"
          @input="submitted = false"
        />
        <Transition name="field-error">
          <p v-if="hostNameInvalid" class="mt-1.5 text-xs font-medium text-red-600">
            Host name is required.
          </p>
        </Transition>
      </div>

      <div>
        <label class="field-label" for="location-text">Location <span class="text-orange-600">*</span></label>
        <div class="relative">
          <input
            id="location-text"
            v-model="locationText"
            class="app-input pr-8"
            :class="locationInvalid ? 'border-red-400 bg-red-50/40 focus:border-red-500 focus:ring-red-200' : ''"
            placeholder="Neighborhood, city, or full address"
            autocomplete="off"
            @input="submitted = false"
            @keydown="onLocationKeydown"
            @blur="onLocationBlur"
          />
          <span
            v-if="locationValidation === 'validating'"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 animate-spin select-none pointer-events-none"
          >⟳</span>
          <span
            v-else-if="locationValidation === 'valid'"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-green-500 text-sm select-none pointer-events-none"
          >✓</span>
          <span
            v-else-if="locationValidation === 'invalid'"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-amber-500 text-sm select-none pointer-events-none"
          >⚠</span>

          <ul
            v-if="showSuggestions"
            class="absolute z-20 left-0 right-0 top-full mt-1 bg-white rounded-xl shadow-lg border border-stone-100 overflow-hidden"
          >
            <li
              v-for="(r, i) in locationSuggestions"
              :key="r.display_name"
              @mousedown.prevent="selectSuggestion(r)"
              class="px-4 py-2.5 text-sm cursor-pointer transition-colors flex items-baseline gap-2"
              :class="i === highlightedIndex ? 'bg-orange-50 text-orange-700' : 'text-stone-700 hover:bg-stone-50'"
            >
              <span class="font-medium shrink-0">{{ formatSuggestion(r) }}</span>
              <span class="text-xs text-stone-400 truncate">{{ r.display_name }}</span>
            </li>
          </ul>
        </div>
        <div class="mt-1.5 flex items-center gap-1.5">
          <button
            type="button"
            class="flex items-center gap-1 text-xs text-stone-400 hover:text-orange-600 transition-colors"
            :disabled="geoLoading"
            @click="useCurrentLocation"
          >
            <span v-if="geoLoading" class="animate-spin">⟳</span>
            <svg v-else class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="3" /><path d="M12 2v3m0 14v3M2 12h3m14 0h3" />
            </svg>
            Use my current location
          </button>
        </div>
        <Transition name="field-error">
          <p v-if="geoError" class="mt-1 text-xs font-medium text-red-600">{{ geoError }}</p>
        </Transition>
        <Transition name="field-error">
          <p v-if="locationInvalid" class="mt-1.5 text-xs font-medium text-red-600">
            Location is required.
          </p>
        </Transition>
        <Transition name="field-error">
          <p v-if="locationValidation === 'invalid' && !locationInvalid" class="mt-1.5 text-xs font-medium text-amber-600">
            No restaurants found here — try a nearby city or neighborhood.
          </p>
        </Transition>
      </div>

      <div>
        <div class="flex items-baseline justify-between">
          <label class="field-label" for="radius-miles">Search Radius <span class="text-orange-600">*</span></label>
          <span class="text-xs font-medium text-stone-500">{{ radiusMiles }} mi</span>
        </div>
        <input
          id="radius-miles"
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
          <label class="field-label" for="cuisine">Cuisine <span class="ml-1 normal-case text-[0.65rem] font-medium tracking-normal text-stone-400">Optional</span></label>
          <input
            id="cuisine"
            v-model="cuisine"
            class="app-input"
            placeholder="Sushi, burgers, tapas..."
          />
        </div>
        <div>
          <label class="field-label">Budget <span class="ml-1 normal-case text-[0.65rem] font-medium tracking-normal text-stone-400">Optional</span></label>
          <div class="mt-1.5 flex gap-2">
            <button
              v-for="(label, tier) in ['$', '$$', '$$$', '$$$$']"
              :key="tier"
              type="button"
              class="flex-1 rounded-full border py-1.5 text-sm font-medium transition-colors"
              :class="selectedPriceTiers.includes(tier + 1)
                ? 'border-orange-400 bg-orange-50 text-orange-700'
                : 'border-stone-200 bg-white text-stone-500 hover:border-stone-300 hover:text-stone-700'"
              @click="selectedPriceTiers.includes(tier + 1)
                ? selectedPriceTiers.splice(selectedPriceTiers.indexOf(tier + 1), 1)
                : selectedPriceTiers.push(tier + 1)"
            >
              {{ label }}
            </button>
          </div>
        </div>
      </div>

      <p class="text-xs text-stone-400"><span class="text-orange-600">*</span> Required</p>
      <button
        :disabled="store.loading"
        class="app-button w-full"
        type="submit"
      >
        {{ store.loading ? "Creating..." : "Create Session" }}
      </button>
    </form>
  </section>
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

.field-error-enter-active,
.field-error-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.field-error-enter-from,
.field-error-leave-to {
  opacity: 0;
  transform: translateY(-2px);
}
</style>
