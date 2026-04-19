import { StrictMode } from 'react'

import { createRoot } from 'react-dom/client'

import '@mantine/charts/styles.css'
import { MantineProvider } from '@mantine/core'
import '@mantine/core/styles.css'
import '@mantine/dates/styles.css'

import App from './App.tsx'
import './index.css'
import theme from './theme.ts'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MantineProvider theme={theme} defaultColorScheme="light">
      <App />
    </MantineProvider>
  </StrictMode>,
)
