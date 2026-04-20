<script setup lang="ts">
import { ref } from "vue";

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

async function submit() {
  if (!hostName.value.trim() || !locationText.value.trim()) {
    return;
  }
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
        <p class="section-copy">Set the mood, location, and filters. We’ll turn that into a room everyone can jump into fast.</p>
      </div>
      <span class="status-pill">Host Flow</span>
    </div>
    <form class="mt-4 space-y-4" @submit.prevent="submit">
      <div>
        <label class="field-label" for="host-name">Host Name</label>
        <input
          id="host-name"
          v-model="hostName"
          class="app-input"
          placeholder="Who is leading tonight?"
        />
      </div>
      <div>
        <label class="field-label" for="location-text">Location</label>
        <input
          id="location-text"
          v-model="locationText"
          class="app-input"
          placeholder="Neighborhood, city, or full address"
        />
      </div>
      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="field-label" for="cuisine">Cuisine</label>
          <input
            id="cuisine"
            v-model="cuisine"
            class="app-input"
            placeholder="Sushi, burgers, tapas..."
          />
        </div>
        <div>
          <label class="field-label" for="price">Budget</label>
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
        <label class="field-label" for="radius-miles">Search Radius</label>
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
