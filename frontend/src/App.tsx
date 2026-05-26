import { Route, Routes } from 'react-router-dom'

import Dashboard from '@pages/Dashboard.tsx'
import LandingPage from '@pages/LandingPage.tsx'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/dashboard" element={<Dashboard />} />
    </Routes>
  )
}

export default App
