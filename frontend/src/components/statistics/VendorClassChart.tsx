import React from 'react'

import { useTranslation } from 'react-i18next'

import type { Organization } from '@models/organization'
import { vendorClassLabel } from '@utils/categoryUtils'
import { vendorClassDistribution } from '@utils/mailInsights'

import styles from './VendorClassChart.module.scss'

type Props = {
  orgs: Organization[]
}

const SIZE = 260
const STROKE = 48
const RADIUS = (SIZE - STROKE) / 2
const CENTER = SIZE / 2
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const GAP = 5

const VendorClassChart = ({ orgs }: Props): React.ReactElement => {
  const { t } = useTranslation('statistics')
  const { t: tMail } = useTranslation('mail')
  const distribution = vendorClassDistribution(orgs).filter((entry) => entry.count > 0)

  let offset = 0
  const segments = distribution.map((entry) => {
    const length = entry.share * CIRCUMFERENCE
    const segment = { ...entry, length, offset }
    offset += length
    return segment
  })

  return (
    <div className={styles.card}>
      <p className={styles.title}>{t('vendorClassTitle')}</p>
      <div className={styles.body}>
        <svg className={styles.chart} width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
          <g transform={`rotate(-90 ${CENTER} ${CENTER})`}>
            <circle cx={CENTER} cy={CENTER} r={RADIUS} fill="none" stroke="#f1f3f5" strokeWidth={STROKE} />
            {segments.map((segment) => {
              const visible = Math.max(segment.length - GAP, 1)
              return (
                <circle
                  key={segment.key}
                  cx={CENTER}
                  cy={CENTER}
                  r={RADIUS}
                  fill="none"
                  stroke={segment.color}
                  strokeWidth={STROKE}
                  strokeDasharray={`${visible} ${CIRCUMFERENCE - visible}`}
                  strokeDashoffset={-segment.offset}
                />
              )
            })}
          </g>
        </svg>
        <ul className={styles.legend}>
          {distribution.map((entry) => (
            <li key={entry.key} className={styles.legendItem}>
              <span className={styles.dot} style={{ background: entry.color }} />
              <span className={styles.legendLabel}>{vendorClassLabel(tMail, entry.key)}</span>
              <span className={styles.legendValue}>{Math.round(entry.share * 100)}%</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default VendorClassChart
