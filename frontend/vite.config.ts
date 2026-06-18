import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

// API_PROXY_TARGET is set in docker-compose.dev.yml for Docker networking.
// Defaults to localhost for local development without Docker.
const apiTarget = process.env.API_PROXY_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 3000,
    proxy: {
      "/api": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/widget": {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
});
