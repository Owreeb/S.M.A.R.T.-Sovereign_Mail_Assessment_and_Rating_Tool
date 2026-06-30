import { useEffect } from 'react'

import dayjs from 'dayjs'
import L from 'leaflet'
import 'leaflet.markercluster'
import { useTranslation } from 'react-i18next'
import { useMap } from 'react-leaflet'

import type { MailSystem, MailSystemRole, MappableOrganization } from '@models/organization'
import { categoryLabel } from '@utils/categoryUtils'
import { roleGroups, vendorCategoryMeta } from '@utils/mailInsights'
import { sovereigntyColor, sovereigntyLevel } from '@utils/sovereignty'

import styles from './ClusteredMarkers.module.scss'

type CategoryKey = 'catPublic' | 'catEuVendor' | 'catEuSub' | 'catIntl' | 'catHyperscaler' | 'catUnknown'

type PopupLabels = {
  sovereignty: string
  lastChecked: string
  levelLabel: string
  grade: (score: number) => string
  category: string
  roles: Record<MailSystemRole, string>
  categories: Record<CategoryKey, string>
  unidentified: string
  via: (name: string) => string
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

const renderFlags = (codes: string[]): string =>
  codes.length
    ? `<span class="${styles.flags}">${codes
        .map((code) => `<span class="fi fi-${escapeHtml(code.toLowerCase())}" title="${escapeHtml(code)}"></span>`)
        .join('')}</span>`
    : ''

const renderSystem = (system: MailSystem, labels: PopupLabels): string => {
  const meta = vendorCategoryMeta(system.vendor_category)
  const name = system.software ?? labels.unidentified
  const badge = `<span class="${styles.badge}" style="color:${meta.color};background:${meta.color}1a">${escapeHtml(
    labels.categories[meta.key as CategoryKey],
  )}</span>`
  const proxy = system.proxy
    ? `<div class="${styles.proxy}">${escapeHtml(labels.via(system.proxy.software ?? '—'))} ${renderFlags(
        system.proxy.countries,
      )}</div>`
    : ''
  return `<div class="${styles.system}">
      <span class="${styles.sysName}">${escapeHtml(name)}</span>
      ${badge}
      ${renderFlags(system.countries)}
      ${proxy}
    </div>`
}

const renderMailFlow = (org: MappableOrganization, labels: PopupLabels): string => {
  const groups = roleGroups(org)
  if (!groups.length) return ''
  const rows = groups
    .map(
      (group) => `
      <div class="${styles.flowRow}">
        <span class="${styles.roleLabel}">${escapeHtml(labels.roles[group.role])}</span>
        <div class="${styles.systems}">${group.systems.map((s) => renderSystem(s, labels)).join('')}</div>
      </div>`,
    )
    .join('')
  return `<div class="${styles.flow}">${rows}</div>`
}

const renderPopup = (org: MappableOrganization, labels: PopupLabels): string => {
  const index = org.sovereignty_index
  const color = sovereigntyColor(index)
  const scoreText = index == null ? labels.levelLabel : `${labels.levelLabel} (${labels.grade(index)})`
  const domain = org.domain ?? org.email_domain
  const checked = org.last_checked ? dayjs(org.last_checked).format('DD.MM.YYYY HH:mm') : '—'

  const domainRow = domain ? `<p class="${styles.domain}">${escapeHtml(domain)}</p>` : ''

  return `
    <div class="${styles.popup}">
      <p class="${styles.title}">${escapeHtml(org.org)}</p>
      ${domainRow}
      <span class="${styles.category}">${escapeHtml(labels.category)}</span>
      <div class="${styles.row}">
        <span class="${styles.label}">${escapeHtml(labels.sovereignty)}</span>
        <span class="${styles.score}" style="color: ${color}">${escapeHtml(scoreText)}</span>
      </div>
      ${renderMailFlow(org, labels)}
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
  const { t: tMail } = useTranslation('mail')
  const { t: tCommon } = useTranslation('common')

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
          lastChecked: t('popupLastChecked'),
          levelLabel: t(`levels.${sovereigntyLevel(org.sovereignty_index)}`),
          grade: (score: number) => tCommon('grade', { score }),
          category: categoryLabel(t, org.category),
          roles: {
            smtp_in: tMail('roles.smtp_in'),
            imap_pop3: tMail('roles.imap_pop3'),
            smtp_out: tMail('roles.smtp_out'),
            webmailer: tMail('roles.webmailer'),
          },
          categories: {
            catPublic: tMail('catPublic'),
            catEuVendor: tMail('catEuVendor'),
            catEuSub: tMail('catEuSub'),
            catIntl: tMail('catIntl'),
            catHyperscaler: tMail('catHyperscaler'),
            catUnknown: tMail('catUnknown'),
          },
          unidentified: tMail('unidentified'),
          via: (name: string) => tMail('via', { name }),
        }),
      )
      cluster.addLayer(marker)
    })

    map.addLayer(cluster)

    return () => {
      map.removeLayer(cluster)
    }
  }, [map, orgs, t, tMail, tCommon])

  return null
}

export default ClusteredMarkers
