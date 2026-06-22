<template>
  <div class="min-h-screen bg-gray-50">
    <nav v-if="apiKeySet" class="bg-monero-dark shadow-lg sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <router-link to="/" class="flex items-center space-x-2">
            <Landmark class="text-white" :size="24" />
            <span class="text-white font-bold text-lg">XMRFTS</span>
          </router-link>
          <div class="flex items-center space-x-4">
            <router-link
              to="/news"
              class="nav-link"
              :class="{
                'text-white bg-monero-orange/20 rounded-md':
                  $route.path === '/news',
              }"
            >
              <div class="flex items-center space-x-1">
                <Newspaper :size="16" />
                <span>News</span>
              </div>
            </router-link>
            <router-link
              to="/widget"
              class="nav-link"
              :class="{
                'text-white bg-monero-orange/20 rounded-md':
                  $route.path === '/widget',
              }"
            >
              <div class="flex items-center space-x-1">
                <Code2 :size="16" />
                <span>Widget</span>
              </div>
            </router-link>
            <router-link
              to="/settings"
              class="nav-link"
              :class="{
                'text-white bg-monero-orange/20 rounded-md':
                  $route.path === '/settings',
              }"
            >
              <div class="flex items-center space-x-1">
                <Settings :size="16" />
                <span>Settings</span>
              </div>
            </router-link>
            <button
              class="text-gray-400 hover:text-red-400 text-sm ml-4 transition-colors flex items-center space-x-1"
              title="Disconnect"
              @click="handleLogout"
            >
              <LogOut :size="14" />
              <span>Disconnect</span>
            </button>
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-24">
      <router-view />
    </main>

    <footer
      class="border-t border-gray-200 py-4 text-center text-sm text-gray-500"
    >
      XMR Fund Transparency Suite
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { Landmark, Settings, Code2, LogOut, Newspaper } from "@lucide/vue";
import { useFundStore } from "@/stores/fund";

const router = useRouter();
const store = useFundStore();
const apiKeySet = computed(() => store.apiKeySet);

function handleLogout() {
  store.logout();
  router.push("/");
}
</script>

<style scoped>
.nav-link {
  @apply text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors;
}
</style>
