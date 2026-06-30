import { Suspense, lazy } from 'react'

import { Route, Routes } from 'react-router-dom'

import Loading from '@components/common/Loading.tsx'
import About from '@pages/About.tsx'
import LandingPage from '@pages/LandingPage.tsx'

const Dashboard = lazy(() => import('@pages/Dashboard.tsx'))

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </Suspense>
  )
}

export default App
