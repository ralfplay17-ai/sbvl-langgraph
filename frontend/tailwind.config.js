/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#0f0f0e',
        card: '#1c1c1b',
        border: '#2e2e2c',
        muted: '#6b6b65',
        buy: {
          bg: '#e8f5dc',
          text: '#356b1f',
          border: '#5ca22d',
        },
        hold: {
          bg: '#fff5df',
          text: '#80500e',
          border: '#f0a92f',
        },
        sell: {
          bg: '#ffe5e3',
          text: '#8c1f1a',
          border: '#d94841',
        },
      },
    },
  },
  plugins: [],
}
