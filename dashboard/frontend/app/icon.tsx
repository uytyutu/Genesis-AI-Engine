import { ImageResponse } from "next/og";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

/** Favicon — Orbit Stack v1.0 FROZEN (compact geometry @32px) */
export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          position: "relative",
          background: "linear-gradient(135deg, #5b8def 0%, #4f46e5 100%)",
          borderRadius: 14,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 15,
            top: 38,
            width: 34,
            height: 7,
            borderRadius: 3,
            background: "rgba(255,255,255,0.38)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 18,
            top: 30,
            width: 28,
            height: 7,
            borderRadius: 3,
            background: "rgba(255,255,255,0.62)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 21,
            top: 22,
            width: 22,
            height: 7,
            borderRadius: 3,
            background: "rgba(255,255,255,0.96)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 17,
            top: 44,
            width: 9,
            height: 9,
            borderRadius: 9,
            background: "#fff",
          }}
        />
      </div>
    ),
    { ...size }
  );
}
