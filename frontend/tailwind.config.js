/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50:  '#effcf9',
          100: '#c8f7ec',
          200: '#91efda',
          300: '#52e0c4',
          400: '#24c9ab',
          500: '#0ea892',
          600: '#098878',
          700: '#0b6d62',
          800: '#0e5750',
          900: '#114843',
          950: '#032c29',
        },
        sentiment: {
          negative: '#ef4444',
          'negative-light': '#fca5a5',
          neutral: '#eab308',
          'neutral-light': '#fde68a',
          positive: '#22c55e',
          'positive-light': '#86efac',
        },
        uk: {
          royal: '#1d4ed8',
          'royal-light': '#93c5fd',
          heritage: '#7c2d12',
          'heritage-light': '#fed7aa',
          slate: '#475569',
          'slate-light': '#cbd5e1',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
