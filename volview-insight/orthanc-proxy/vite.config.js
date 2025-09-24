import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      "/dicom-web": {
        target: process.env.ORTHANC_URL || "http://localhost:8042",
        changeOrigin: true,
        // auth: "orthanc:orthanc",
        configure: (proxy) => {
        // proxy will be an instance of 'http-proxy'
          proxy.on("proxyRes", function (proxyRes, req, res) {
            res.setHeader("Access-Control-Allow-Origin", "*");
            res.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
          });
        },
      },
    },
  },
});
