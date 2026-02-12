<script setup lang="ts">
import { computed, ref } from "vue";

import CreateSessionView from "./views/CreateSessionView.vue";
import JoinSessionView from "./views/JoinSessionView.vue";
import SwipeSessionView from "./views/SwipeSessionView.vue";
import WaitingRoomView from "./views/WaitingRoomView.vue";
import { useSessionStore } from "./stores/session";

const store = useSessionStore();
const mode = ref<"create" | "join">("create");

const inSession = computed(() => Boolean(store.session));
const inActiveSession = computed(() => store.session?.status === "active");
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-xl">
      <h1 class="text-3xl font-bold tracking-tight text-slate-900">Grubble</h1>
      <p class="mt-1 text-sm text-slate-600">Restaurant group decision app</p>

      <p v-if="store.error" class="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
        {{ store.error }}
      </p>

      <SwipeSessionView v-if="inActiveSession" class="mt-6" />
      <WaitingRoomView v-else-if="inSession" class="mt-6" />

      <section v-else class="mt-6 space-y-4">
        <div class="inline-flex rounded-md bg-slate-200 p-1">
          <button
            class="rounded px-4 py-2 text-sm font-medium"
            :class="mode === 'create' ? 'bg-white text-slate-900 shadow' : 'text-slate-600'"
            @click="mode = 'create'"
          >
            Create
          </button>
          <button
            class="rounded px-4 py-2 text-sm font-medium"
            :class="mode === 'join' ? 'bg-white text-slate-900 shadow' : 'text-slate-600'"
            @click="mode = 'join'"
          >
            Join
          </button>
        </div>

        <CreateSessionView v-if="mode === 'create'" @created="() => {}" />
        <JoinSessionView v-else @joined="() => {}" />
      </section>
    </div>
  </main>
</template>
