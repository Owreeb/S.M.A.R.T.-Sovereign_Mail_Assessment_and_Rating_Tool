import { createTheme } from '@mantine/core'

const theme = createTheme({
  primaryColor: 'green',
  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif',
  defaultRadius: 'md',
  colors: {
    green: [
      '#ebfbee',
      '#d3f9d8',
      '#b2f2bb',
      '#8ce99a',
      '#69db7c',
      '#51cf66',
      '#40c057',
      '#37b24d',
      '#2f9e44',
      '#2b8a3e',
    ],
  },
  components: {
    Paper: {
      defaultProps: {
        bg: 'white',
      },
    },
  },
})

export default theme
