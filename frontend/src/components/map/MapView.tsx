import React, { useMemo, useState } from 'react'

import L from 'leaflet'
import 'leaflet-geosearch/dist/geosearch.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'
import 'leaflet/dist/leaflet.css'
import { useTranslation } from 'react-i18next'
import { MapContainer, TileLayer } from 'react-leaflet'

import type { Organization } from '@models/organization'
import { IconFilter } from '@tabler/icons-react'

import ClusteredMarkers from './ClusteredMarkers'
import FilterPanel from './FilterPanel'
import Legend from './Legend'
import styles from './MapView.module.scss'
import SearchControl from './SearchControl'
import { FILTER_FIELDS, type FilterState } from './filterFields'

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl
L.Icon.Default.mergeOptions({ iconRetinaUrl, iconUrl, shadowUrl })

type Props = {
  orgs: Organization[]
}

const emptyFilterState = (): FilterState => Object.fromEntries(FILTER_FIELDS.map((field) => [field.key, []]))

const MapView = ({ orgs }: Props): React.ReactElement => {
  const { t } = useTranslation('map')
  const [selected, setSelected] = useState<FilterState>(emptyFilterState)
  const [filterOpen, setFilterOpen] = useState(false)

  const activeCount = FILTER_FIELDS.reduce((sum, field) => sum + selected[field.key].length, 0)

  const filteredOrgs = useMemo(
    () =>
      orgs.filter((org) =>
        FILTER_FIELDS.every((field) => {
          const chosen = selected[field.key]
          if (chosen.length === 0) return true
          const value = org[field.key]
          return Array.isArray(value) ? value.some((v) => chosen.includes(v)) : chosen.includes(value)
        }),
      ),
    [orgs, selected],
  )

  const toggleValue = (key: string, value: string): void =>
    setSelected((prev) => {
      const current = prev[key]
      const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value]
      return { ...prev, [key]: next }
    })

  return (
    <div className={styles.wrapper}>
      <div className={styles.map}>
        <MapContainer center={[51.16, 10.45]} zoom={6} scrollWheelZoom style={{ width: '100%', height: '100%' }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
            subdomains={['a', 'b', 'c', 'd']}
            maxZoom={19}
          />
          <SearchControl />
          <ClusteredMarkers orgs={filteredOrgs} />
        </MapContainer>
        <Legend />
        {!filterOpen && (
          <button type="button" className={styles.filterToggle} onClick={() => setFilterOpen(true)}>
            <IconFilter size={16} />
            <span>{t('filter')}</span>
            {activeCount > 0 && <span className={styles.toggleBadge}>{activeCount}</span>}
          </button>
        )}
        <FilterPanel
          orgs={orgs}
          selected={selected}
          open={filterOpen}
          onToggle={toggleValue}
          onReset={() => setSelected(emptyFilterState())}
          onClose={() => setFilterOpen(false)}
        />
      </div>
    </div>
  )
}

export default MapView
