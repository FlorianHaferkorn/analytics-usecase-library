import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          mint: "#47D7AC",
          petrol: "#06041F",
          nightfall: "#13294B",
          limestone: "#C4C9D2",
          lavender: "#2E008B",
          yellow: "#FBD872",
          pink: "#F8485E",
        },
        nagarro: {
          green: {
            900: "#205463",
            700: "#2D807B",
            500: "#3AAB94",
            400: "#47D7AC",
            300: "#75E1C1",
            200: "#A3EBD5",
            100: "#D1F5EA",
          },
          blue: {
            900: "#06041F",
            700: "#13294B",
            500: "#4E5E78",
            300: "#8893A5",
          },
          gray: {
            400: "#C4C9D2",
            300: "#D2D6DD",
            200: "#E0E3E8",
            100: "#EFF1F4",
            50: "#F7F8F9",
          },
          purple: {
            900: "#2E008B",
            700: "#6240A8",
            500: "#9680C5",
            300: "#CBBFE2",
          },
          yellow: {
            700: "#F99068",
            500: "#FBD872",
            300: "#FCE195",
            100: "#FDF4DC",
          },
          pink: {
            900: "#4C3150",
            700: "#863854",
            500: "#BF4059",
            400: "#F8485E",
            300: "#F97586",
            200: "#FBA3AF",
            100: "#FCD0D7",
          },
        },
        // Semantic colors that flip with dark mode
        surface: {
          DEFAULT: "#FFFFFF",
          secondary: "#F7F8F9",
          tertiary: "#EFF1F4",
          dark: "#06041F",
          "dark-secondary": "#0D0B2E",
          "dark-tertiary": "#13294B",
        },
        content: {
          DEFAULT: "#06041F",
          secondary: "#4E5E78",
          tertiary: "#8893A5",
          inverse: "#FFFFFF",
          "inverse-secondary": "#C4C9D2",
        },
        border: {
          DEFAULT: "#E0E3E8",
          dark: "#1E2A45",
        },
        signal: {
          positive: "#16A34A",
          negative: "#DC2626",
          warning: "#D97706",
          info: "#47D7AC",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
