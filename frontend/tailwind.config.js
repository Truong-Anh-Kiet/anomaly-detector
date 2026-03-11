/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        anomaly: {
          light: '#fef3c7',
          normal: '#fbbf24',
          medium: '#f97316',
          high: '#dc2626',
        }
      },
    },
  },
  plugins: [],
}
