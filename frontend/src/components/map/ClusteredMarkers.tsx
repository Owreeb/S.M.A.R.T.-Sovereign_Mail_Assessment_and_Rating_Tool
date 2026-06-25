import { useEffect } from 'react'

import dayjs from 'dayjs'
import L from 'leaflet'
import 'leaflet.markercluster'
import { useTranslation } from 'react-i18next'
import { useMap } from 'react-leaflet'

import type { MappableOrganization } from '@models/organization'
import { categoryLabel } from '@utils/categoryUtils'
import { sovereigntyColor, sovereigntyLevel } from '@utils/sovereignty'

import styles from './ClusteredMarkers.module.scss'

type PopupLabels = {
  sovereignty: string
  providers: string
  lastChecked: string
  levelLabel: string
  category: string
}

type Props = {
  orgs: MappableOrganization[]
}

const escapeHtml = (value: string): string =>
  value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

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

const renderPopup = (org: MappableOrganization, labels: PopupLabels): string => {
  const index = org.sovereignty_index
  const color = sovereigntyColor(index)
  const scoreText = index == null ? labels.levelLabel : `${labels.levelLabel} (${index}/6)`
  const domain = org.domain ?? org.email_domain
  const checked = org.last_checked ? dayjs(org.last_checked).format('DD.MM.YYYY HH:mm') : '—'

  const domainRow = domain ? `<p class="${styles.domain}">${escapeHtml(domain)}</p>` : ''
  const providersRow = org.providers.length
    ? `<div class="${styles.row}">
        <span class="${styles.label}">${escapeHtml(labels.providers)}</span>
        <span>${escapeHtml(org.providers.join(', '))}</span>
      </div>`
    : ''

  return `
    <div class="${styles.popup}">
      <p class="${styles.title}">${escapeHtml(org.org)}</p>
      ${domainRow}
      <span class="${styles.category}">${escapeHtml(labels.category)}</span>
      <div class="${styles.row}">
        <span class="${styles.label}">${escapeHtml(labels.sovereignty)}</span>
        <span class="${styles.score}" style="color: ${color}">${escapeHtml(scoreText)}</span>
      </div>
      ${providersRow}
      <div class="${styles.row}">
        <span class="${styles.label}">${escapeHtml(labels.lastChecked)}</span>
        <span>${escapeHtml(checked)}</span>
      </div>
    </div>
  `
}

const ClusteredMarkers = ({ orgs }: Props): null => {
  const map = useMap()
  const { t } = useTranslation('map')

  useEffect(() => {
    const cluster = L.markerClusterGroup({
      showCoverageOnHover: false,
      spiderfyOnMaxZoom: true,
    })

    orgs.forEach((org) => {
      const marker = L.marker([org.lat, org.long], {
        title: org.org,
        icon: createIcon(sovereigntyColor(org.sovereignty_index)),
      })
      marker.bindPopup(
        renderPopup(org, {
          sovereignty: t('popupSovereignty'),
          providers: t('popupProviders'),
          lastChecked: t('popupLastChecked'),
          levelLabel: t(`levels.${sovereigntyLevel(org.sovereignty_index)}`),
          category: categoryLabel(t, org.category),
        }),
      )
      cluster.addLayer(marker)
    })

    map.addLayer(cluster)

    return () => {
      map.removeLayer(cluster)
    }
  }, [map, orgs, t])

  return null
}

export default ClusteredMarkers
