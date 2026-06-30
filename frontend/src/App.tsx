import { Route, Routes } from 'react-router-dom'

import Dashboard from '@pages/Dashboard.tsx'
import LandingPage from '@pages/LandingPage.tsx'
import About from '@pages/About.tsx'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/about" element={<About />} />
    </Routes>
  )
}

export default App
