import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    allowedHosts: ["goliath"],
    proxy: {
      "/api": {
        target: "http://localhost:7771",
        changeOrigin: true,
      },
      "/socket.io": {
        target: "http://localhost:7771",
        ws: true,
      },
    },
  },
});
