import { ImageResponse } from "next/og";

export const alt = "Genesis AI Engine";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(160deg, #0a0a0f 0%, #111118 50%, #1a1a2e 100%)",
          color: "#ececf1",
        }}
      >
        <div
          style={{
            width: 160,
            height: 160,
            borderRadius: 36,
            background: "linear-gradient(135deg, #5b8def 0%, #4f46e5 100%)",
            display: "flex",
            position: "relative",
          }}
        >
          <div style={{ position: "absolute", left: 38, top: 95, width: 85, height: 16, borderRadius: 8, background: "rgba(255,255,255,0.38)" }} />
          <div style={{ position: "absolute", left: 45, top: 76, width: 70, height: 16, borderRadius: 8, background: "rgba(255,255,255,0.62)" }} />
          <div style={{ position: "absolute", left: 52, top: 56, width: 55, height: 16, borderRadius: 8, background: "rgba(255,255,255,0.96)" }} />
          <div style={{ position: "absolute", left: 42, top: 110, width: 22, height: 22, borderRadius: 22, background: "#fff" }} />
        </div>
        <div style={{ marginTop: 40, fontSize: 56, fontWeight: 700 }}>Genesis AI Engine</div>
        <div style={{ marginTop: 12, fontSize: 28, color: "#8b8b9a" }}>Company OS for digital business</div>
      </div>
    ),
    { ...size }
  );
}
