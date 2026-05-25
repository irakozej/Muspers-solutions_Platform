/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        musper: {
          green: '#1F4E3D',
          'green-dark': '#163A2D',
          'green-light': '#2C6B55',
          orange: '#E07B1F',
          'orange-dark': '#B8631A',
          bg: '#F8F8F5',
          ink: '#1A1A1A',
          muted: '#6B6B6B',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      letterSpacing: {
        tightish: '-0.015em',
      },
    },
  },
  plugins: [],
};
