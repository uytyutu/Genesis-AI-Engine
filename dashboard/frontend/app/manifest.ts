import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Genesis AI Engine",
    short_name: "Genesis",
    description: "Company OS — websites and digital services for small business",
    start_url: "/site",
    display: "standalone",
    background_color: "#050508",
    theme_color: "#4f46e5",
    icons: [
      {
        src: "/brand/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/brand/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
