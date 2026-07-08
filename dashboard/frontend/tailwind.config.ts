/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        genesis: {
          bg: "#050508",
          surface: "#0c0c12",
          panel: "#111118",
          elevated: "#18181f",
          border: "#27272f",
          "border-subtle": "#1c1c24",
          accent: "#5b8def",
          "accent-soft": "#3d6fd4",
          purple: "#a78bfa",
          "purple-soft": "#7c3aed",
          green: "#34d399",
          amber: "#fbbf24",
          rose: "#fb7185",
          muted: "#8b8b9a",
          text: "#ececf1",
        },
      },
      boxShadow: {
        glow: "0 0 40px -12px rgba(91, 141, 239, 0.35)",
        card: "0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 32px -8px rgba(0,0,0,0.6)",
        "card-hover": "0 1px 0 rgba(255,255,255,0.06) inset, 0 12px 40px -12px rgba(0,0,0,0.7)",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.25rem",
        "4xl": "1.5rem",
      },
      animation: {
        "fade-up": "fadeUp 0.5s ease-out forwards",
        "fade-in": "fadeIn 0.4s ease-out forwards",
        "slide-in-right": "slideInRight 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "pulse-soft": "pulseSoft 2.5s ease-in-out infinite",
        "genesis-voice-bar": "genesisVoiceBar 0.9s ease-in-out infinite",
        "genesis-voice-orb": "genesisVoiceOrb 1.8s ease-in-out infinite",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.55" },
        },
        genesisVoiceBar: {
          "0%, 100%": { transform: "scaleY(0.45)", opacity: "0.5" },
          "50%": { transform: "scaleY(1)", opacity: "1" },
        },
        genesisVoiceOrb: {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.08)" },
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
