import React from 'react'

import Loading from '@components/common/Loading.tsx'
import Footer from '@components/landing/Footer.tsx'
import Navbar from '@components/landing/Navbar.tsx'
import MapView from '@components/map/MapView.tsx'
import InsightsSection from '@components/statistics/InsightsSection.tsx'
import OverviewSection from '@components/statistics/OverviewSection.tsx'
import OrgTable from '@components/table/OrgTable.tsx'
import { useDeferredMount } from '@hooks/useDeferredMount.ts'
import { useOrgFilters } from '@hooks/useOrgFilters.ts'
import type { Organization } from '@models/organization.ts'
import type { StatisticsData } from '@models/statisticsData.ts'

import organizationsData from '../data/organizations.json'

const dataFiles = import.meta.glob('../data/[0-9]*.json', { eager: true, import: 'default' })
const sortedFiles = Object.keys(dataFiles)
  .filter((path) => !path.includes('EXAMPLE'))
  .sort((a, b) => b.localeCompare(a))

const currentData = dataFiles[sortedFiles[0]] as StatisticsData
const previousData = dataFiles[sortedFiles[1]] as StatisticsData | undefined
const organizations = (organizationsData as Organization[]).filter((org) => org.sovereignty_index != null)

const Dashboard = (): React.ReactElement => {
  const ready = useDeferredMount()
  const filters = useOrgFilters(organizations)

  return (
    <>
      <Navbar />
      {ready ? (
        <>
          <OverviewSection currentData={currentData} previousData={previousData} orgs={organizations} />
          <InsightsSection orgs={organizations} />
          <MapView orgs={organizations} filters={filters} />
          <OrgTable orgs={filters.filteredOrgs} filters={filters} />
        </>
      ) : (
        <Loading />
      )}
      <Footer />
    </>
  )
}

export default Dashboard
