import { useEffect } from 'react'

import dayjs from 'dayjs'
import L from 'leaflet'
import 'leaflet.markercluster'
import { useMap } from 'react-leaflet'

import type { Organization } from '@models/organization'

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

const scoreColor = (index: number): string => {
  if (index >= 9) return '#1c7ed6' // Blau
  if (index >= 8) return '#2f9e44' // Grün
  if (index >= 6) return '#74b816' // Hellgrün
  if (index >= 4) return '#f2cc0c' // Gelb
  if (index >= 2) return '#f76707' // Orange
  return '#e03131' // Rot
}

const createIcon = (color: string): L.DivIcon =>
  L.divIcon({
    className: styles.pin,
    html: `<svg width="24" height="36" viewBox="0 0 24 36" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 8.25 12 24 12 24s12-15.75 12-24C24 5.37 18.63 0 12 0z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/>
      <circle cx="12" cy="12" r="4.5" fill="#ffffff"/>
    </svg>`,
    iconSize: [24, 36],
    iconAnchor: [12, 36],
    popupAnchor: [0, -34],
  })

const renderPopup = (org: Organization): string => {
  const checked = dayjs(org.last_checked).format('DD.MM.YYYY HH:mm')
  return `
    <div class="${styles.popup}">
      <p class="${styles.title}">${escapeHtml(org.org)}</p>
      <p class="${styles.domain}">${escapeHtml(org.domain)}</p>
      <span class="${styles.category}">${escapeHtml(org.category)}</span>
      <div class="${styles.row}">
        <span class="${styles.label}">Souveränität</span>
        <span class="${styles.score}" style="color: ${scoreColor(org.sovereignty_index)}">
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
      const marker = L.marker([org.lat, org.long], {
        title: org.org,
        icon: createIcon(scoreColor(org.sovereignty_index)),
      })
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
