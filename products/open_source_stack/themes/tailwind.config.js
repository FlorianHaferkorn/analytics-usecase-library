/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['../evidence_app/**/*.{html,md,svelte}'],
  theme: {
    extend: {
      colors: {
        // Governed design tokens — match theme_config.json
        primary: 'var(--color-primary, #003366)',
        'brand-header': 'var(--color-brand-header, #1a1a2e)',
        surface: 'var(--color-surface, #f8f9fa)',
      },
      fill: {
        primary: 'var(--color-primary, #003366)',
      },
      textColor: {
        'brand-header': 'var(--color-brand-header, #1a1a2e)',
      },
      backgroundColor: {
        surface: 'var(--color-surface, #f8f9fa)',
      },
    },
  },
  plugins: [],
};
