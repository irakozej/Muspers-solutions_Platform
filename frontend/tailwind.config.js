/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    container: {
      center: true,
      padding: {
        DEFAULT: '1.25rem',
        sm: '2rem',
        lg: '3rem',
        xl: '4rem',
      },
      screens: {
        '2xl': '1280px',
      },
    },
    extend: {
      colors: {
        musper: {
          green: '#1F4E3D',
          'green-deep': '#16382B',
          'green-mid': '#2C6B55',
          'green-soft': 'rgba(31, 78, 61, 0.08)',
          orange: '#E07B1F',
          'orange-dark': '#B8631A',
          'orange-soft': 'rgba(224, 123, 31, 0.10)',
          cream: '#F5F2EA',
          'cream-soft': '#FBF9F4',
          ink: '#161616',
          muted: '#6B6B6B',
          'muted-soft': '#9A9591',
          line: 'rgba(22, 22, 22, 0.08)',
          'line-on-dark': 'rgba(245, 242, 234, 0.14)',
        },
      },
      fontFamily: {
        display: ['"Fraunces"', 'ui-serif', 'Georgia', 'Cambria', 'serif'],
        sans: ['"Geist"', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"Geist Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      letterSpacing: {
        tightish: '-0.015em',
        editorial: '-0.025em',
        eyebrow: '0.18em',
      },
      fontSize: {
        eyebrow: ['0.72rem', { lineHeight: '1', letterSpacing: '0.18em' }],
        'display-sm': ['2.5rem', { lineHeight: '1.05', letterSpacing: '-0.02em' }],
        display: ['3.5rem', { lineHeight: '1.02', letterSpacing: '-0.025em' }],
        'display-lg': ['5rem', { lineHeight: '0.98', letterSpacing: '-0.03em' }],
        'display-xl': ['7rem', { lineHeight: '0.94', letterSpacing: '-0.035em' }],
      },
      boxShadow: {
        soft: '0 1px 0 rgba(22,22,22,0.04), 0 18px 40px -22px rgba(22,22,22,0.18)',
        ring: '0 0 0 1px rgba(31,78,61,0.18)',
        cta: '0 18px 42px -18px rgba(224,123,31,0.55)',
      },
      backgroundImage: {
        'grain': "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.45 0'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='0.18'/></svg>\")",
      },
      transitionTimingFunction: {
        editorial: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
    },
  },
  plugins: [],
};
