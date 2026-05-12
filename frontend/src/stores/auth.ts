import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type { User } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const loading = ref(true);

  const isLoggedIn = computed(() => !!user.value);
  const displayName = computed<string>(
    () => (user.value?.user_metadata?.display_name as string) ?? ""
  );

  async function init() {
    const { data } = await supabase.auth.getSession();
    user.value = data.session?.user ?? null;
    loading.value = false;
    supabase.auth.onAuthStateChange((_event, session) => {
      user.value = session?.user ?? null;
    });
  }

  async function signUp(email: string, password: string, name: string = "") {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { display_name: name.trim() } },
    });
    if (error) throw error;
  }

  async function signIn(email: string, password: string) {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  }

  async function signOut() {
    await supabase.auth.signOut();
  }

  async function updateDisplayName(name: string) {
    const { error } = await supabase.auth.updateUser({
      data: { display_name: name.trim() },
    });
    if (error) throw error;
  }

  return { user, loading, isLoggedIn, displayName, init, signUp, signIn, signOut, updateDisplayName };
});
