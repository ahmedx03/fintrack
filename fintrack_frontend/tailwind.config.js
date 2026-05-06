/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Navy — dark blue for navbar & strong headers
        navy: {
          700: '#1e3a5f',
          800: '#162d4a',
          900: '#0d1b2e',
        },
        // Brand — medium blue for buttons, highlights, links
        brand: {
          50:  '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // Aqua — light tints for backgrounds and accents
        aqua: {
          50:  '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'auth-gradient':
          'linear-gradient(135deg, #0d1b2e 0%, #162d4a 35%, #1a5276 65%, #0e7490 100%)',
        'app-bg':
          'linear-gradient(160deg, #eff6ff 0%, #e0f2fe 50%, #f0f9ff 100%)',
      },
    },
  },
  plugins: [],
}
