import { ImageResponse } from "next/og";

export const alt = "Virtus Core";
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
          background: "#050508",
          color: "#ececf1",
        }}
      >
        <div
          style={{
            width: 160,
            height: 160,
            borderRadius: 36,
            background: "#0c0c14",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            position: "relative",
          }}
        >
          <div
            style={{
              position: "absolute",
              left: 28,
              top: 24,
              width: 48,
              height: 88,
              borderRadius: 28,
              background: "#e4e4ea",
              transform: "rotate(-18deg)",
            }}
          />
          <div
            style={{
              position: "absolute",
              right: 28,
              top: 24,
              width: 48,
              height: 88,
              borderRadius: 28,
              background: "#e4e4ea",
              transform: "rotate(18deg)",
            }}
          />
          <div
            style={{
              position: "absolute",
              bottom: 22,
              width: 36,
              height: 36,
              borderRadius: 36,
              background: "#e4e4ea",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div style={{ width: 18, height: 18, borderRadius: 18, background: "#7c8fd4" }} />
          </div>
        </div>
        <div style={{ marginTop: 40, fontSize: 56, fontWeight: 700 }}>Virtus Core</div>
        <div style={{ marginTop: 12, fontSize: 28, color: "#8b8b9a" }}>Vector · Digital Company</div>
      </div>
    ),
    { ...size }
  );
}
