/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#2d5016',
        accent: '#C8891A',
        'accent-gold': '#d4af37',
        parchment: '#F5F0E8',
        'background-light': '#f7f8f6',
        'background-dark': '#181f13',
        sage: '#738268',
        'border-muted': '#e0e4dd',
      },
      fontFamily: {
        display: ['Work Sans', 'sans-serif'],
        sans: ['Work Sans', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        lg: '1rem',
        xl: '1.5rem',
        full: '9999px',
      },
    },
  },
  plugins: [],
}

