import { Route, Routes } from 'react-router-dom'

import Dashboard from '@pages/Dashboard.tsx'
import LandingPage from '@pages/LandingPage.tsx'
import ScoreInfo from '@pages/ScoreInfo.tsx'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/score-info" element={<ScoreInfo />} />
    </Routes>
  )
}

export default App
