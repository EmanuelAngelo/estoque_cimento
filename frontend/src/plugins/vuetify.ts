/**
 * plugins/vuetify.ts
 *
 * Framework documentation: https://vuetifyjs.com
 */

import { createVuetify } from 'vuetify'
import '@mdi/font/css/materialdesignicons.css'
import '../styles/layers.css'
import 'vuetify/styles'

export default createVuetify({
  defaults: {
    VApp: {
      fullHeight: true,
    },
    VContainer: {
      fluid: false,
    },
    VCard: {
      rounded: 'xl',
      elevation: 0,
      border: false,
    },
    VToolbar: {
      flat: true,
      density: 'comfortable',
    },
    VBtn: {
      rounded: 'xl',
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VDataTable: {
      density: 'comfortable',
    },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          background: 'hsl(220 20% 97%)',
          surface: 'hsl(0 0% 100%)',
          primary: 'hsl(220 70% 50%)',
          secondary: 'hsl(220 15% 45%)',
          success: 'hsl(160 60% 42%)',
          info: 'hsl(210 90% 55%)',
          warning: 'hsl(35 90% 52%)',
          error: 'hsl(0 70% 50%)',
        },
      },
    },
    utilities: false,
  },
  display: {
    mobileBreakpoint: 'md',
    thresholds: {
      xs: 0,
      sm: 600,
      md: 840,
      lg: 1145,
      xl: 1545,
      xxl: 2138,
    },
  },
})
