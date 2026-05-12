<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { deleteSession, getMySessions } from "../lib/api";
import type { SessionSummary } from "../types";
import { useAuthStore } from "../stores/auth";
import { useSessionStore } from "../stores/session";

const auth = useAuthStore();
const store = useSessionStore();

const hosted = ref<SessionSummary[]>([]);
const joined = ref<SessionSummary[]>([]);
const loading = ref(true);
const error = ref("");
const rejoinLoading = ref<string | null>(null);
const removingParticipant = ref<string | null>(null);
const expandedParticipants = ref<Set<string>>(new Set());

function toggleParticipants(roomCode: string) {
  const next = new Set(expandedParticipants.value);
  if (next.has(roomCode)) {
    next.delete(roomCode);
  } else {
    next.add(roomCode);
  }
  expandedParticipants.value = next;
}

let pollTimer: ReturnType<typeof setInterval> | null = null;

function hasLiveSessions() {
  return hosted.value.some((s) => s.status === "waiting" || s.status === "active");
}

onMounted(async () => {
  try {
    const data = await getMySessions();
    hosted.value = data.hosted;
    joined.value = data.joined;
  } catch {
    error.value = "Could not load session history.";
  } finally {
    loading.value = false;
  }

  pollTimer = setInterval(async () => {
    if (hasLiveSessions()) {
      await reload().catch(() => {});
    }
  }, 5000);
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});

async function reload() {
  const data = await getMySessions();
  hosted.value = data.hosted;
  joined.value = data.joined;
}

async function remove(roomCode: string) {
  try {
    await deleteSession(roomCode);
    hosted.value = hosted.value.filter((s) => s.room_code !== roomCode);
  } catch {
    error.value = "Could not delete session.";
  }
}

async function rejoin(roomCode: string, name: string) {
  error.value = "";
  rejoinLoading.value = roomCode;
  try {
    await store.join(roomCode, name);
  } catch {
    error.value = "Could not rejoin session.";
  } finally {
    rejoinLoading.value = null;
  }
}

async function kickParticipant(roomCode: string, userName: string) {
  removingParticipant.value = `${roomCode}:${userName}`;
  try {
    await store.removeParticipant(roomCode, userName);
    await reload();
  } catch {
    error.value = "Could not remove participant.";
  } finally {
    removingParticipant.value = null;
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

const statusLabel: Record<string, string> = {
  waiting: "Waiting",
  active: "Active",
  ended: "Ended",
  paused: "Paused",
};
</script>

<template>
  <section class="glass-card mt-5">
    <h2 class="section-title text-stone-900">My Sessions</h2>

    <div v-if="loading" class="mt-4 text-sm text-stone-400">Loading...</div>

    <div v-else-if="error" class="mt-4 text-sm text-red-600">{{ error }}</div>

    <div v-else-if="hosted.length === 0 && joined.length === 0" class="mt-4 text-sm text-stone-400">
      No sessions yet. Create one above to get started.
    </div>

    <div v-else class="mt-4 space-y-6">
      <div v-if="hosted.length > 0">
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-400">Hosted</p>
        <ul class="space-y-2">
          <li
            v-for="s in hosted"
            :key="s.room_code"
            class="rounded-xl border border-stone-100 bg-white px-4 py-3"
          >
            <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-stone-800">{{ s.location_text ?? "No location" }}</p>
                <p class="text-xs text-stone-400">
                  {{ formatDate(s.created_at) }} · {{ s.participant_count }} participant{{ s.participant_count !== 1 ? "s" : "" }}
                  · <span :class="s.status === 'active' ? 'text-green-600' : 'text-stone-400'">{{ statusLabel[s.status] ?? s.status }}</span>
                </p>
              </div>
              <div class="flex flex-wrap gap-2 sm:shrink-0 sm:justify-end">
                <button
                  v-if="s.status !== 'ended'"
                  :disabled="rejoinLoading === s.room_code"
                  class="rounded-lg border border-orange-200 bg-orange-50 px-3 py-1 text-xs font-medium text-orange-700 transition-colors hover:bg-orange-100 disabled:opacity-50"
                  @click="rejoin(s.room_code, s.host_name)"
                >
                  {{ rejoinLoading === s.room_code ? "Joining..." : "Rejoin" }}
                </button>
                <button
                  v-if="s.participants?.length"
                  class="rounded-lg border border-stone-200 bg-white px-3 py-1 text-xs font-medium text-stone-600 transition-colors hover:border-stone-300 hover:text-stone-800"
                  @click="toggleParticipants(s.room_code)"
                >
                  {{ expandedParticipants.has(s.room_code) ? "Hide Participants" : "View Participants" }}
                </button>
                <button
                  class="rounded-lg border border-red-200 bg-red-50 px-3 py-1 text-xs font-medium text-red-600 transition-colors hover:bg-red-100"
                  @click="remove(s.room_code)"
                >
                  Delete
                </button>
              </div>
            </div>

            <!-- Participant management for waiting sessions -->
            <div v-if="s.participants?.length && expandedParticipants.has(s.room_code)" class="mt-3 border-t border-stone-100 pt-3">
              <p class="mb-1.5 text-xs font-medium text-stone-400">Participants</p>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="p in s.participants"
                  :key="p.user_name"
                  class="inline-flex items-center gap-1 rounded-full bg-stone-50 px-2.5 py-1 text-xs text-stone-600"
                >
                  {{ p.user_name }}
                  <span v-if="p.user_name === s.host_name" class="text-orange-400">·host</span>
                  <button
                    v-else
                    :disabled="removingParticipant === `${s.room_code}:${p.user_name}`"
                    class="ml-0.5 text-stone-300 transition-colors hover:text-red-500 disabled:opacity-40"
                    :aria-label="`Remove ${p.user_name}`"
                    @click="kickParticipant(s.room_code, p.user_name)"
                  >×</button>
                </span>
              </div>
            </div>
          </li>
        </ul>
      </div>

      <div v-if="joined.length > 0">
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-400">Joined</p>
        <ul class="space-y-2">
          <li
            v-for="s in joined"
            :key="s.room_code"
            class="flex items-center justify-between gap-3 rounded-xl border border-stone-100 bg-white px-4 py-3"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-stone-800">{{ s.location_text ?? "No location" }}</p>
              <p class="text-xs text-stone-400">
                Hosted by {{ s.host_name }} · {{ formatDate(s.created_at) }}
                · <span :class="s.status === 'active' ? 'text-green-600' : 'text-stone-400'">{{ statusLabel[s.status] ?? s.status }}</span>
              </p>
            </div>
            <button
              v-if="s.status !== 'ended'"
              :disabled="rejoinLoading === s.room_code"
              class="shrink-0 rounded-lg border border-orange-200 bg-orange-50 px-3 py-1 text-xs font-medium text-orange-700 transition-colors hover:bg-orange-100 disabled:opacity-50"
              @click="rejoin(s.room_code, s.my_participant_name ?? auth.displayName)"
            >
              {{ rejoinLoading === s.room_code ? "Joining..." : "Rejoin" }}
            </button>
          </li>
        </ul>
      </div>
    </div>
  </section>

</template>
