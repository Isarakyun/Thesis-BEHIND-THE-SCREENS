/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    'web/templates/*.html', // Add all relevant file types and directories
    'src/*.{html,js,ts,jsx,tsx}', // Keep this if you also have these file types in the src directory
  ],
  theme: {
    extend: {
      screens: {
        'widescreen': { 'raw': '(min-aspect-ratio: 3/2)' },
        'tallscreen': { 'raw': '(min-aspect-ratio: 1/2)' },
      },
    },
  },
  plugins: [],
}