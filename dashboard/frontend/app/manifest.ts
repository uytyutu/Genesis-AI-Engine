import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Virtus Core",
    short_name: "Virtus",
    description: "Virtus Core — Vector intelligent AI assistant",
    start_url: "/site",
    display: "standalone",
    background_color: "#050508",
    theme_color: "#7c8fd4",
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
