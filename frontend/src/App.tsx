import StatisticsGrid from '@components/statistics/StatisticsGrid.tsx'
import type { StatisticsData } from '@models/statisticsData.ts'

const dataFiles = import.meta.glob('./data/*.json', { eager: true, import: 'default' })
const sortedFiles = Object.keys(dataFiles).sort().reverse()

const currentData = dataFiles[sortedFiles[0]] as StatisticsData
const previousData = dataFiles[sortedFiles[1]] as StatisticsData | undefined

function App() {
  return (
    <>
      <StatisticsGrid currentData={currentData} previousData={previousData} />
    </>
  )
}

export default App
