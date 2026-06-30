import React from 'react'

import { useTranslation } from 'react-i18next'

import type { Organization } from '@models/organization'
import { categoryLabel } from '@utils/categoryUtils'
import { tierColor } from '@utils/countryUtils'
import { hostingResidency, scoreHistogram, sovereigntyBySector } from '@utils/mailInsights'
import { sovereigntyColor } from '@utils/sovereignty'

import styles from './InsightsSection.module.scss'

type Props = {
  orgs: Organization[]
}

type Row = { key: string; label: string; value: string; ratio: number; color: string }

const BarList = ({ title, rows }: { title: string; rows: Row[] }): React.ReactElement => (
  <div className={styles.block}>
    <p className={styles.blockTitle}>{title}</p>
    {rows.map((row) => (
      <div key={row.key} className={styles.row}>
        <span className={styles.label}>{row.label}</span>
        <div className={styles.track}>
          <div className={styles.bar} style={{ width: `${Math.max(row.ratio * 100, 1)}%`, background: row.color }} />
        </div>
        <span className={styles.value}>{row.value}</span>
      </div>
    ))}
  </div>
)

const RESIDENCY_KEY = {
  de: 'resDe',
  eu: 'resEu',
  other: 'resOther',
  us: 'resUs',
} as const

const InsightsSection = ({ orgs }: Props): React.ReactElement => {
  const { t } = useTranslation(['statistics', 'common'])
  const { t: tMap } = useTranslation('map')

  const histogram = scoreHistogram(orgs)
  const maxScoreCount = Math.max(1, ...histogram.map((b) => b.count))
  const scoreRows: Row[] = histogram.map((bucket) => ({
    key: String(bucket.index),
    label: t('common:grade', { score: bucket.index }),
    value: bucket.count.toLocaleString(),
    ratio: bucket.count / maxScoreCount,
    color: sovereigntyColor(bucket.index),
  }))

  const sectorRows: Row[] = sovereigntyBySector(orgs).map((sector) => ({
    key: sector.category,
    label: categoryLabel(tMap, sector.category),
    value: sector.average.toFixed(2),
    ratio: sector.average / 6,
    color: sovereigntyColor(Math.round(sector.average)),
  }))

  const residencyRows: Row[] = hostingResidency(orgs).map((tier) => ({
    key: tier.tier,
    label: t(RESIDENCY_KEY[tier.tier]),
    value: `${Math.round(tier.share * 100)}%`,
    ratio: tier.share,
    color: tierColor(tier.tier),
  }))

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>{t('insightsTitle')}</h2>
      <div className={styles.grid}>
        <BarList title={t('scoreDistTitle')} rows={scoreRows} />
        <BarList title={t('bySectorTitle')} rows={sectorRows} />
        <BarList title={t('residencyTitle')} rows={residencyRows} />
      </div>
    </section>
  )
}

export default InsightsSection
