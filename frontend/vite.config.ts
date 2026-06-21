import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

// API_PROXY_TARGET is set via docker-compose.yml for Docker networking.
// Defaults to localhost for local development without Docker.
const apiTarget = process.env.API_PROXY_TARGET || "http://localhost:8000";
const appUrl = process.env.APP_URL || "localhost";

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
    allowedHosts: [appUrl, "localhost"],
    proxy: {
      "/api": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/widget": {
        target: apiTarget,
        changeOrigin: true,
        // Proxy API requests for widget data; let the SPA handle /widget page routes
        bypass: (req) => {
          if (
            !req.url?.match(/^\/widget\/[^/]+\.(js|json)$/) &&
            !req.url?.match(/^\/widget\/[^/]+\/export\//)
          ) {
            return req.url;
          }
        },
      },
    },
  },
});
