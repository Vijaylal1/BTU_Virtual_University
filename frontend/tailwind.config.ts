import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        deep:    '#0a0a18',
        card:    '#12122a',
        sidebar: '#0d0d24',
        bpurple: '#7c5cbf',
        blight:  '#9b7de0',
        bgreen:  '#3ecf8e',
        bcoral:  '#ff6b6b',
        byellow: '#ffd93d',
        bblue:   '#4facfe',
        bmuted:  '#8892a4',
        btext:   '#e2e8f0',
      },
      keyframes: {
        bounce3: {
          '0%, 60%, 100%': { transform: 'translateY(0)' },
          '30%':            { transform: 'translateY(-6px)' },
        },
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        toastIn: {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        bounce3: 'bounce3 1.2s infinite',
        fadeUp:  'fadeUp 0.3s ease',
        toastIn: 'toastIn 0.3s ease',
      },
    },
  },
  plugins: [],
}

export default config
