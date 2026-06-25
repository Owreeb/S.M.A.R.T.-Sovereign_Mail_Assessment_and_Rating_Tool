/// <reference types="vitest/config" />
import path from 'path'
import { defineConfig } from 'vite'

import babel from '@rolldown/plugin-babel'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  // Served from https://owreeb.github.io/SMART/ in production, root in dev.
  base: command === 'build' ? '/SMART/' : '/',
  plugins: [react(), babel({ presets: [reactCompilerPreset()] })],
  server: {
    fs: {
      allow: ['..'],
    },
  },
  test: {
    coverage: {
      reporter: ['lcov'],
      exclude: ['src/__tests__/**'],
    },
  },
  resolve: {
    alias: {
      '@assets': path.resolve(__dirname, 'src/assets'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@constants': path.resolve(__dirname, 'src/constants'),
      '@hooks': path.resolve(__dirname, 'src/hooks'),
      '@models': path.resolve(__dirname, 'src/models'),
      '@pages': path.resolve(__dirname, 'src/pages'),
      '@utils': path.resolve(__dirname, 'src/utils'),
    },
  },
}))
