<script setup lang="ts">
import { computed, ref } from "vue";

import CreateSessionView from "./views/CreateSessionView.vue";
import JoinSessionView from "./views/JoinSessionView.vue";
import ResultsSessionView from "./views/ResultsSessionView.vue";
import SwipeSessionView from "./views/SwipeSessionView.vue";
import WaitingRoomView from "./views/WaitingRoomView.vue";
import { useSessionStore } from "./stores/session";

const store = useSessionStore();
const mode = ref<"create" | "join">("create");

const inSession = computed(() => Boolean(store.session));
const inActiveSession = computed(() => store.session?.status === "active");
</script>

<template>
  <main class="app-shell min-h-screen">
    <div class="hero-panel">
      <p class="hero-kicker">Group Dinner, Simplified</p>
      <h1 class="hero-title text-stone-900">Grubble</h1>
      <p class="hero-subtitle">
        Gather the group, narrow the neighborhood, and let the best spot rise to the top without the usual back-and-forth.
      </p>

      <p v-if="store.error" class="soft-alert mt-6 bg-red-50 text-red-700">
        {{ store.error }}
      </p>

      <ResultsSessionView v-if="inActiveSession && store.showResults" class="mt-6" />
      <SwipeSessionView v-else-if="inActiveSession" class="mt-6" />
      <WaitingRoomView v-else-if="inSession" class="mt-6" />

      <section v-else class="mt-8 space-y-5">
        <div class="segmented-shell">
          <button
            class="segmented-button"
            :class="mode === 'create' ? 'segmented-button-active' : ''"
            @click="mode = 'create'"
          >
            Create
          </button>
          <button
            class="segmented-button"
            :class="mode === 'join' ? 'segmented-button-active' : ''"
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
