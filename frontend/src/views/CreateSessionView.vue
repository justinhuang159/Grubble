<script setup lang="ts">
import { ref, computed } from "vue";

import { useSessionStore } from "../stores/session";

const emit = defineEmits<{
  created: [];
}>();

const store = useSessionStore();
const hostName = ref("");
const locationText = ref("");
const cuisine = ref("");
const price = ref("");
const radiusMiles = ref();
const submitted = ref(false);

const hostNameInvalid = computed(() => submitted.value && !hostName.value.trim());
const locationInvalid = computed(() => submitted.value && !locationText.value.trim());
const hasErrors = computed(() => hostNameInvalid.value || locationInvalid.value);

async function submit() {
  submitted.value = true;
  if (hasErrors.value) return;
  await store.create({
    host_name: hostName.value,
    location_text: locationText.value,
    cuisine: cuisine.value || undefined,
    price: price.value || undefined,
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
        <input
          id="location-text"
          v-model="locationText"
          class="app-input"
          :class="locationInvalid ? 'border-red-400 bg-red-50/40 focus:border-red-500 focus:ring-red-200' : ''"
          placeholder="Neighborhood, city, or full address"
          @input="submitted = false"
        />
        <Transition name="field-error">
          <p v-if="locationInvalid" class="mt-1.5 text-xs font-medium text-red-600">
            Location is required.
          </p>
        </Transition>
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
          <label class="field-label" for="price">Budget <span class="ml-1 normal-case text-[0.65rem] font-medium tracking-normal text-stone-400">Optional</span></label>
          <select
            id="price"
            v-model="price"
            class="app-input bg-white/80"
          >
            <option value="">Any budget</option>
            <option value="1">$</option>
            <option value="1,2">$$ and under</option>
            <option value="2,3">$$$ and under</option>
            <option value="3,4">$$$$ only</option>
          </select>
        </div>
      </div>

      <div>
        <label class="field-label" for="radius-miles">Search Radius <span class="ml-1 normal-case text-[0.65rem] font-medium tracking-normal text-stone-400">Optional</span></label>
        <input
          id="radius-miles"
          v-model.number="radiusMiles"
          class="app-input"
          min="0"
          max="25"
          step="0.5"
          type="number"
          placeholder="Miles from the chosen location"
        />
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
