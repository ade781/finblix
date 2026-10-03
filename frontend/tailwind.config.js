/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        finblix: {
          bg: "#090d16",
          card: "#111827",
          border: "#1f2937",
          accent: "#3b82f6",
          bullish: "#10b981",
          bearish: "#f43f5e",
          warning: "#f59e0b",
          muted: "#94a3b8"
        }
      }
    },
  },
  plugins: [],
}
