/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        void:    '#020408',
        deep:    '#050d14',
        panel:   '#080f18',
        card:    '#0b1520',
        hover:   '#0f1e2e',
        border:  '#0d2438',
        borderB: '#0f3a5a',
        cyan:    '#00d4ff',
        green:   '#00ff9d',
        red:     '#ff2d55',
        amber:   '#ffaa00',
        purple:  '#a855f7',
        textP:   '#c8e6f5',
        textS:   '#5a8ba8',
        textD:   '#2a4a62',
      },
      fontFamily: {
        mono:    ['"Share Tech Mono"', 'monospace'],
        raj:     ['Rajdhani', 'sans-serif'],
        orb:     ['Orbitron', 'monospace'],
      }
    }
  },
  plugins: []
}