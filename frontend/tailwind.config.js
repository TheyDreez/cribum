/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        graphite: {
          950: '#0b0d10',
          900: '#111418',
          850: '#171b21',
          800: '#1e232b',
          700: '#2c333e',
        },
        auditTeal: {
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
        },
        auditAmber: {
          400: '#fbbf24',
          500: '#f59e0b',
        },
        auditRose: {
          500: '#f43f5e',
          600: '#e11d48',
        }
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
