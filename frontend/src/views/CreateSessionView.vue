<script setup lang="ts">
import { computed, ref } from "vue";

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

const hostNameError = computed(() => {
  if (!submitted.value) {
    return "";
  }
  return hostName.value.trim() ? "" : "Host name is required.";
});

const locationError = computed(() => {
  if (!submitted.value) {
    return "";
  }
  return locationText.value.trim() ? "" : "Location is required.";
});

async function submit() {
  submitted.value = true;
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
  <section class="rounded-xl bg-white p-6 shadow">
    <h2 class="text-xl font-semibold text-slate-900">Create Session</h2>
    <p class="mt-1 text-sm text-slate-600">Create a room and become host.</p>
    <form class="mt-4 space-y-4" @submit.prevent="submit">
      <input
        v-model="hostName"
        :class="[
          'w-full rounded-md border px-3 py-2 outline-none focus:border-slate-500',
          hostNameError ? 'border-red-400 focus:border-red-500' : 'border-slate-300',
        ]"
        placeholder="Host name"
      />
      <p v-if="hostNameError" class="text-xs text-red-600">{{ hostNameError }}</p>
      <input
        v-model="locationText"
        :class="[
          'w-full rounded-md border px-3 py-2 outline-none focus:border-slate-500',
          locationError ? 'border-red-400 focus:border-red-500' : 'border-slate-300',
        ]"
        placeholder="Location (e.g. San Francisco, CA)"
      />
      <p v-if="locationError" class="text-xs text-red-600">{{ locationError }}</p>
      <input
        v-model="cuisine"
        class="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
        placeholder="Cuisine (optional, e.g. sushi)"
      />
      <select
        v-model="price"
        class="w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-slate-500"
      >
        <option value="">Price (optional)</option>
        <option value="1">$</option>
        <option value="1,2">$$ and under</option>
        <option value="2,3">$$$ and under</option>
        <option value="3,4">$$$$ only</option>
      </select>
      <input
        v-model.number="radiusMiles"
        class="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
        min="0"
        max="25"
        step="0.5"
        type="number"
        placeholder="Radius miles (optional)"
      />
      <button
        :disabled="store.loading"
        class="w-full rounded-md bg-slate-900 px-4 py-2 font-medium text-white disabled:opacity-60"
        type="submit"
      >
        {{ store.loading ? "Creating..." : "Create Session" }}
      </button>
    </form>
  </section>
</template>
