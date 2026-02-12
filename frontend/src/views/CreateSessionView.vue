<script setup lang="ts">
import { ref } from "vue";

import { useSessionStore } from "../stores/session";

const emit = defineEmits<{
  created: [];
}>();

const store = useSessionStore();
const hostName = ref("");

async function submit() {
  if (!hostName.value.trim()) {
    return;
  }
  await store.create(hostName.value);
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
        class="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
        placeholder="Host name"
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
