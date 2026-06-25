import { StrictMode } from 'react'

import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import { MantineProvider } from '@mantine/core'
import '@mantine/core/styles.css'

import App from './App.tsx'
import './i18n/i18n'
import './index.css'
import theme from './theme.ts'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MantineProvider theme={theme} defaultColorScheme="light">
      <BrowserRouter basename={import.meta.env.BASE_URL}>
        <App />
      </BrowserRouter>
    </MantineProvider>
  </StrictMode>,
)
