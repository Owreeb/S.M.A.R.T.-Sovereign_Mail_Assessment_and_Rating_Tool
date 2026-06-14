import React from 'react'

import type { ParseKeys, TFunction } from 'i18next'

import type { Organization } from '@models/organization'
import { scoreColor } from '@utils/sovereignty'

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

const statusClass: Record<Organization['sovereignty_level'], string> = {
  high: styles.statusHigh,
  medium: styles.statusMedium,
  low: styles.statusLow,
}

const statusKey: Record<Organization['sovereignty_level'], TableKey> = {
  high: 'statusHigh',
  medium: 'statusMedium',
  low: 'statusLow',
}

export const TABLE_COLUMNS: TableColumn[] = [
  {
    key: 'domain',
    labelKey: 'colDomain',
    accessor: (org) => org.domain,
    render: (org) => <span className={styles.domain}>{org.domain}</span>,
  },
  { key: 'org', labelKey: 'colOrg', accessor: (org) => org.org },
  { key: 'category', labelKey: 'colCategory', accessor: (org) => org.category },
  { key: 'provider', labelKey: 'colProvider', accessor: (org) => org.provider.join(', ') },
  { key: 'smtp', labelKey: 'colSmtp', accessor: (org) => org.smtp_software.join(', ') },
  {
    key: 'status',
    labelKey: 'colStatus',
    accessor: (org) => org.sovereignty_level,
    render: (org, t) => (
      <span className={`${styles.status} ${statusClass[org.sovereignty_level]}`}>
        {t(statusKey[org.sovereignty_level])}
      </span>
    ),
  },
  {
    key: 'score',
    labelKey: 'colScore',
    accessor: (org) => org.sovereignty_index.toFixed(1),
    render: (org) => (
      <span className={styles.score} style={{ color: scoreColor(org.sovereignty_index) }}>
        {org.sovereignty_index.toFixed(1)}
      </span>
    ),
  },
  { key: 'country', labelKey: 'colCountry', accessor: (org) => org.provider_country },
]
