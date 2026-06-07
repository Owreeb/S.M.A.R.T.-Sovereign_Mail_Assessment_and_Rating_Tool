import React from 'react'

import L from 'leaflet'
import 'leaflet-geosearch/dist/geosearch.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'
import 'leaflet/dist/leaflet.css'
import { MapContainer, TileLayer } from 'react-leaflet'

import type { Organization } from '@models/organization'

import ClusteredMarkers from './ClusteredMarkers'
import Legend from './Legend'
import styles from './MapView.module.scss'
import SearchControl from './SearchControl'

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl
L.Icon.Default.mergeOptions({ iconRetinaUrl, iconUrl, shadowUrl })

type Props = {
  orgs: Organization[]
}

const MapView = ({ orgs }: Props): React.ReactElement => {
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
          <ClusteredMarkers orgs={orgs} />
        </MapContainer>
        <Legend />
      </div>
    </div>
  )
}

export default MapView
