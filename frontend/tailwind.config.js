/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bond-bg': '#0f172a',
        'bond-card': 'rgba(30, 41, 59, 0.7)',
        'bond-primary': '#38bdf8',
        'bond-secondary': '#818cf8',
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
