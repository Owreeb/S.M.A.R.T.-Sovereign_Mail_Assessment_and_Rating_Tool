import { useEffect } from 'react'

import dayjs from 'dayjs'
import L from 'leaflet'
import 'leaflet.markercluster'
import { useMap } from 'react-leaflet'

import type { Organization, SovereigntyLevel } from '@models/organization'

import styles from './ClusteredMarkers.module.scss'

type Props = {
  orgs: Organization[]
}

const escapeHtml = (value: string): string =>
  value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

const levelClass: Record<SovereigntyLevel, string> = {
  high: styles.high,
  medium: styles.medium,
  low: styles.low,
}

const renderPopup = (org: Organization): string => {
  const checked = dayjs(org.last_checked).format('DD.MM.YYYY HH:mm')
  return `
    <div class="${styles.popup}">
      <p class="${styles.title}">${escapeHtml(org.org)}</p>
      <p class="${styles.domain}">${escapeHtml(org.domain)}</p>
      <span class="${styles.category}">${escapeHtml(org.category)}</span>
      <div class="${styles.row}">
        <span class="${styles.label}">Souveränität</span>
        <span class="${levelClass[org.sovereignty_level]}">
          ${org.sovereignty_index.toFixed(1)} / ${escapeHtml(org.sovereignty_level)}
        </span>
      </div>
      <div class="${styles.row}">
        <span class="${styles.label}">Zuletzt geprüft</span>
        <span>${escapeHtml(checked)}</span>
      </div>
    </div>
  `
}

const ClusteredMarkers = ({ orgs }: Props): null => {
  const map = useMap()

  useEffect(() => {
    const cluster = L.markerClusterGroup({
      showCoverageOnHover: false,
      spiderfyOnMaxZoom: true,
    })

    orgs.forEach((org) => {
      const marker = L.marker([org.lat, org.long], { title: org.org })
      marker.bindPopup(renderPopup(org))
      cluster.addLayer(marker)
    })

    map.addLayer(cluster)

    return () => {
      map.removeLayer(cluster)
    }
  }, [map, orgs])

  return null
}

export default ClusteredMarkers
