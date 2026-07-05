import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: false,
};

const theme = extendTheme({
  config,
  colors: {
    brand: {
      50: '#f3e8ff',
      100: '#e4ccff',
      200: '#d1a3ff',
      300: '#bd79ff',
      400: '#aa50ff',
      500: '#aa3bff',
      600: '#8a1fe0',
      700: '#6b17ad',
      800: '#4d107a',
      900: '#2f0947',
    },
    accent: {
      500: '#ec4899',
      600: '#db2777',
    },
  },
  fonts: {
    heading: `'Segoe UI', system-ui, sans-serif`,
    body: `'Segoe UI', system-ui, sans-serif`,
  },
  styles: {
    global: {
      body: {
        bg: 'gray.50',
        color: 'gray.800',
      },
    },
  },
  components: {
    Button: {
      baseStyle: {
        borderRadius: 'xl',
        fontWeight: 'semibold',
      },
    },
  },
});

export default theme;
