import React from 'react'

import type { ParseKeys, TFunction } from 'i18next'

import type { Organization, SovereigntyLevel } from '@models/organization'
import { sovereigntyColor, sovereigntyLevel } from '@utils/sovereignty'

import styles from './OrgTable.module.scss'

type TableKey = ParseKeys<'table'>
type Translate = TFunction<'table'>

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
    render: (org) => (
      <span className={styles.score} style={{ color: sovereigntyColor(org.sovereignty_index) }}>
        {org.sovereignty_index == null ? '—' : `${org.sovereignty_index}/6`}
      </span>
    ),
  },
  { key: 'country', labelKey: 'colCountry', accessor: (org) => org.country ?? '' },
]
