import MapView from '@components/map/MapView.tsx'
import StatisticsGrid from '@components/statistics/StatisticsGrid.tsx'
import type { Organization } from '@models/organization.ts'
import type { StatisticsData } from '@models/statisticsData.ts'

import organizationsData from './data/organizations-EXAMPLE.json'

const dataFiles = import.meta.glob('./data/[0-9]*.json', { eager: true, import: 'default' })
const sortedFiles = Object.keys(dataFiles).sort((a, b) => b.localeCompare(a))

const currentData = dataFiles[sortedFiles[0]] as StatisticsData
const previousData = dataFiles[sortedFiles[1]] as StatisticsData | undefined
const organizations = organizationsData as Organization[]

function App() {
  return (
    <>
      <StatisticsGrid currentData={currentData} previousData={previousData} />
      <MapView orgs={organizations} />
    </>
  )
}

export default App
