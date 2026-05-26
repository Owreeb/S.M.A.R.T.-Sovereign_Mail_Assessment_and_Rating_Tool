import React from 'react'

import FeaturesSection from '@components/landing/FeaturesSection'
import Footer from '@components/landing/Footer'
import Hero from '@components/landing/Hero'
import Navbar from '@components/landing/Navbar'
import SovereigntySection from '@components/landing/SovereigntySection'

const LandingPage = (): React.ReactElement => {
  return (
    <>
      <Navbar />
      <Hero />
      <SovereigntySection />
      <FeaturesSection />
      <Footer />
    </>
  )
}

export default LandingPage
