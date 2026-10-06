import type { Config } from 'tailwindcss'

export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        panel: 'var(--panel)',
        border: 'var(--border)',
        'border-strong': 'var(--border-strong)',
        foreground: 'var(--text-primary)',
        'muted-foreground': 'var(--text-secondary)',
        accent: 'var(--accent)',
        'status-active': 'var(--status-active)',
        'status-suspended': 'var(--status-suspended)',
        'status-offboarded': 'var(--status-offboarded)',
        'status-overdue': 'var(--status-overdue)',
      },
      borderRadius: {
        lg: 'var(--radius)',
      },
      boxShadow: {
        soft: 'var(--shadow-soft)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
} satisfies Config
