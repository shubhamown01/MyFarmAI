/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        /* ========================================================================
           Semantic Color Tokens — Mapped to CSS Variables
           Source: docs/frontend/COLOR_SYSTEM.md
           ======================================================================== */

        /* Core Surface Tokens */
        surface: 'var(--color-surface)',
        'surface-container': 'var(--color-surface-container)',
        'surface-container-low': 'var(--color-surface-container-low)',
        'surface-container-high': 'var(--color-surface-container-high)',
        'surface-container-highest': 'var(--color-surface-container-highest)',

        /* Core Text Tokens */
        'on-surface': 'var(--color-on-surface)',
        'on-surface-variant': 'var(--color-on-surface-variant)',
        'on-surface-disabled': 'var(--color-on-surface-disabled)',

        /* Primary Brand Tokens */
        primary: {
          DEFAULT: 'var(--color-primary)',
          strong: 'var(--color-primary-strong)',
          hover: 'var(--color-primary-hover)',
          active: 'var(--color-primary-active)',
          container: 'var(--color-primary-container)',
          'on-container': 'var(--color-on-primary-container)',
          'on-primary': 'var(--color-on-primary)',
          50: 'var(--color-primary-container)',
          100: '#C8E6C9',
          200: '#A5D6A7',
          300: '#81C784',
          400: '#66BB6A',
          500: '#4CAF50',
          600: '#43A047',
          700: '#388E3C',
          800: 'var(--color-primary)',
          900: 'var(--color-primary-hover)',
        },

        /* Agricultural category tints — used by quick actions and farm tools */
        tint: {
          green: 'var(--color-tint-green)',
          blue: 'var(--color-tint-blue)',
          orange: 'var(--color-tint-orange)',
          purple: 'var(--color-tint-purple)',
          red: 'var(--color-tint-red)',
          neutral: 'var(--color-tint-neutral)',
        },
        icon: {
          green: 'var(--color-icon-green)',
          blue: 'var(--color-icon-blue)',
          orange: 'var(--color-icon-orange)',
          purple: 'var(--color-icon-purple)',
          red: 'var(--color-icon-red)',
        },
        shell: 'var(--color-shell)',

        /* Secondary Tokens */
        secondary: {
          DEFAULT: 'var(--color-secondary)',
          hover: 'var(--color-secondary-hover)',
          container: 'var(--color-secondary-container)',
          'on-container': 'var(--color-on-secondary-container)',
        },

        /* Tertiary Tokens (Info) */
        tertiary: {
          DEFAULT: 'var(--color-tertiary)',
          container: 'var(--color-tertiary-container)',
          'on-container': 'var(--color-on-tertiary-container)',
        },

        /* Success Tokens */
        success: {
          DEFAULT: 'var(--color-success)',
          container: 'var(--color-success-container)',
          'on-container': 'var(--color-on-success-container)',
        },

        /* Warning Tokens */
        warning: {
          DEFAULT: 'var(--color-warning)',
          container: 'var(--color-warning-container)',
          'on-container': 'var(--color-on-warning-container)',
        },

        /* Error Tokens */
        error: {
          DEFAULT: 'var(--color-error)',
          container: 'var(--color-error-container)',
          'on-container': 'var(--color-on-error-container)',
        },

        /* Info Tokens */
        info: {
          DEFAULT: 'var(--color-info)',
          container: 'var(--color-info-container)',
          'on-container': 'var(--color-on-info-container)',
        },

        /* Outline / Border Tokens */
        outline: {
          DEFAULT: 'var(--color-outline)',
          variant: 'var(--color-outline-variant)',
          strong: 'var(--color-outline-strong)',
        },

      },

      /* ========================================================================
         Typography — Font Families and Type Scale
         ======================================================================== */
      fontFamily: {
        sans: ['Inter', 'var(--font-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)'],
      },

      fontSize: {
        'display-large': ['3.5rem', { lineHeight: '1.08', letterSpacing: '-0.03em', fontWeight: '700' }],
        'display-medium': ['2.5rem', { lineHeight: '1.15', letterSpacing: '-0.025em', fontWeight: '700' }],
        'display-small': ['2rem', { lineHeight: '1.2', letterSpacing: '-0.02em', fontWeight: '700' }],
        'headline-large': ['1.5rem', { lineHeight: '1.3', letterSpacing: '-0.015em' }],
        'headline-medium': ['1.25rem', { lineHeight: '1.4', letterSpacing: '-0.01em' }],
        'headline-small': ['1.125rem', { lineHeight: '1.45', letterSpacing: '-0.01em' }],
        'title-large': ['1rem', { lineHeight: '1.5' }],
        'title-medium': ['0.875rem', { lineHeight: '1.5' }],
        'title-small': ['0.8125rem', { lineHeight: '1.5' }],
        'body-large': ['1rem', { lineHeight: '1.6' }],
        'body-medium': ['0.875rem', { lineHeight: '1.6' }],
        'body-small': ['0.8125rem', { lineHeight: '1.5' }],
        'label-large': ['0.875rem', { lineHeight: '1.5' }],
        'label-medium': ['0.8125rem', { lineHeight: '1.5' }],
        'label-small': ['0.75rem', { lineHeight: '1.5' }],
      },

      /* ========================================================================
         Spacing — 4px Base Unit (already covered by Tailwind defaults)
         Custom additions for semantic tokens
         ======================================================================== */
      spacing: {
        '0': 'var(--space-0)',
        '1': 'var(--space-1)',
        '2': 'var(--space-2)',
        '3': 'var(--space-3)',
        '4': 'var(--space-4)',
        '5': 'var(--space-5)',
        '6': 'var(--space-6)',
        '8': 'var(--space-8)',
        '10': 'var(--space-10)',
        '12': 'var(--space-12)',
      },

      /* ========================================================================
         Border Radius Tokens
         ======================================================================== */
      borderRadius: {
        none: 'var(--radius-none)',
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
        full: 'var(--radius-full)',
      },

      /* ========================================================================
         Box Shadow / Elevation Tokens
         ======================================================================== */
      boxShadow: {
        elev0: 'var(--elev-0)',
        elev1: 'var(--elev-1)',
        elev2: 'var(--elev-2)',
        elev3: 'var(--elev-3)',
        elev4: 'var(--elev-4)',
      },

      /* ========================================================================
         Transition Duration Tokens
         ======================================================================== */
      transitionDuration: {
        instant: 'var(--motion-instant)',
        quick: 'var(--motion-quick)',
        fast: 'var(--motion-fast)',
        standard: 'var(--motion-standard)',
        medium: 'var(--motion-medium)',
        slow: 'var(--motion-slow)',
        slower: 'var(--motion-slower)',
      },

      /* ========================================================================
         Transition Timing Functions
         ======================================================================== */
      transitionTimingFunction: {
        'ease-out-quick': 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        'ease-out-standard': 'cubic-bezier(0.0, 0.0, 0.2, 1)',
        'ease-in-out': 'cubic-bezier(0.4, 0.0, 0.2, 1)',
      },
    },
  },
  plugins: [],
};