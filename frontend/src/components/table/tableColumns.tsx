import React from 'react'

import type { ParseKeys, TFunction } from 'i18next'

import type { Organization, SovereigntyLevel } from '@models/organization'
import { hostingCountries, vendorCategoryMeta, worstVendorCategory } from '@utils/mailInsights'
import { sovereigntyColor, sovereigntyLevel } from '@utils/sovereignty'

import styles from './OrgTable.module.scss'

type TableKey = ParseKeys<'table'>
type Translate = TFunction<['table', 'mail', 'common']>

// Add new columns here
export type TableColumn = {
  key: string
  labelKey: TableKey
  accessor: (org: Organization) => string
  render?: (org: Organization, t: Translate) => React.ReactNode
}

const STATUS_KEY: Record<SovereigntyLevel, TableKey> = {
  'sehr-hoch': 'statusVeryHigh',
  hoch: 'statusHigh',
  mittel: 'statusMedium',
  niedrig: 'statusLow',
  'sehr-niedrig': 'statusVeryLow',
  unbekannt: 'statusUnknown',
}

const CATEGORY_KEY: Record<string, TableKey> = {
  hospital: 'catHospital',
  university: 'catUniversity',
  city: 'catCity',
  courthouse: 'catCourthouse',
}

const mailSoftware = (org: Organization): string => {
  const names = new Set<string>()
  Object.values(org.mail_systems).forEach((systems) =>
    systems.forEach((system) => {
      if (system.software) names.add(system.software)
    }),
  )
  return [...names].join(', ')
}

const CATEGORY_TKEY = {
  catPublic: 'mail:catPublic',
  catEuVendor: 'mail:catEuVendor',
  catEuSub: 'mail:catEuSub',
  catIntl: 'mail:catIntl',
  catHyperscaler: 'mail:catHyperscaler',
  catUnknown: 'mail:catUnknown',
} as const

const renderClass = (org: Organization, t: Translate): React.ReactNode => {
  const meta = vendorCategoryMeta(worstVendorCategory(org))
  const key = meta.key as keyof typeof CATEGORY_TKEY
  return (
    <span className={styles.badge} style={{ color: meta.color, background: `${meta.color}1a` }}>
      {t(CATEGORY_TKEY[key])}
    </span>
  )
}

const renderHosting = (org: Organization): React.ReactNode => {
  const codes = hostingCountries(org)
  if (!codes.length) return '—'
  return (
    <span className={styles.hosts}>
      {codes.map((code) => (
        <span key={code} className={`fi fi-${code.toLowerCase()}`} title={code} />
      ))}
    </span>
  )
}

export const TABLE_COLUMNS: TableColumn[] = [
  {
    key: 'domain',
    labelKey: 'colDomain',
    accessor: (org) => org.domain ?? '',
    render: (org) => <span className={styles.domain}>{org.domain ?? '—'}</span>,
  },
  { key: 'org', labelKey: 'colOrg', accessor: (org) => org.org },
  {
    key: 'category',
    labelKey: 'colCategory',
    accessor: (org) => org.category,
    render: (org, t) => {
      const key = CATEGORY_KEY[org.category]
      return key ? t(key) : org.category
    },
  },
  { key: 'provider', labelKey: 'colProvider', accessor: (org) => org.providers.join(', ') },
  { key: 'software', labelKey: 'colSoftware', accessor: mailSoftware },
  {
    key: 'class',
    labelKey: 'colClass',
    accessor: (org) => worstVendorCategory(org) ?? '',
    render: renderClass,
  },
  {
    key: 'hosting',
    labelKey: 'colHosting',
    accessor: (org) => hostingCountries(org).join(' '),
    render: renderHosting,
  },
  {
    key: 'status',
    labelKey: 'colStatus',
    accessor: (org) => sovereigntyLevel(org.sovereignty_index),
    render: (org, t) => (
      <span className={styles.status} style={{ color: sovereigntyColor(org.sovereignty_index) }}>
        {t(STATUS_KEY[sovereigntyLevel(org.sovereignty_index)])}
      </span>
    ),
  },
  {
    key: 'score',
    labelKey: 'colScore',
    accessor: (org) => (org.sovereignty_index == null ? '—' : String(org.sovereignty_index)),
    render: (org, t) => (
      <span className={styles.score} style={{ color: sovereigntyColor(org.sovereignty_index) }}>
        {org.sovereignty_index == null ? '—' : t('common:grade', { score: org.sovereignty_index })}
      </span>
    ),
  },
]
