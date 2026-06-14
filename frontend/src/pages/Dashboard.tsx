import React from 'react'

import Footer from '@components/landing/Footer.tsx'
import Navbar from '@components/landing/Navbar.tsx'
import MapView from '@components/map/MapView.tsx'
import StatisticsGrid from '@components/statistics/StatisticsGrid.tsx'
import OrgTable from '@components/table/OrgTable.tsx'
import { useOrgFilters } from '@hooks/useOrgFilters.ts'
import type { Organization } from '@models/organization.ts'
import type { StatisticsData } from '@models/statisticsData.ts'

import organizationsData from '../data/organizations-EXAMPLE.json'

const dataFiles = import.meta.glob('../data/[0-9]*.json', { eager: true, import: 'default' })
const sortedFiles = Object.keys(dataFiles).sort((a, b) => b.localeCompare(a))

const currentData = dataFiles[sortedFiles[0]] as StatisticsData
const previousData = dataFiles[sortedFiles[1]] as StatisticsData | undefined
const organizations = organizationsData as Organization[]

const Dashboard = (): React.ReactElement => {
  const filters = useOrgFilters(organizations)

  return (
    <>
      <Navbar />
      <StatisticsGrid currentData={currentData} previousData={previousData} />
      <MapView orgs={organizations} filters={filters} />
      <OrgTable orgs={filters.filteredOrgs} filters={filters} />
      <Footer />
    </>
  )
}

export default Dashboard
