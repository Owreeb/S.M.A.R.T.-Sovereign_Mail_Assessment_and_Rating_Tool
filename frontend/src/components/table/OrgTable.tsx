import React, { useMemo, useState } from 'react'

import { useTranslation } from 'react-i18next'

import type { OrgFilters } from '@hooks/useOrgFilters'
import type { Organization } from '@models/organization'
import { IconArrowLeft, IconArrowRight, IconSearch } from '@tabler/icons-react'

import FilterChips from './FilterChips'
import styles from './OrgTable.module.scss'
import { TABLE_COLUMNS } from './tableColumns'

type Props = {
  orgs: Organization[]
  filters: OrgFilters
}

const PAGE_SIZE = 10

const pageItems = (current: number, total: number): (number | 'ellipsis')[] => {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const items: (number | 'ellipsis')[] = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  if (start > 2) items.push('ellipsis')
  for (let i = start; i <= end; i++) items.push(i)
  if (end < total - 1) items.push('ellipsis')
  items.push(total)
  return items
}

const OrgTable = ({ orgs, filters }: Props): React.ReactElement => {
  const { t } = useTranslation('table')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase()
    if (!term) return orgs
    return orgs.filter((org) => TABLE_COLUMNS.some((col) => col.accessor(org).toLowerCase().includes(term)))
  }, [orgs, query])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, pageCount)
  const rows = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const onSearch = (value: string): void => {
    setQuery(value)
    setPage(1)
  }

  return (
    <div className={styles.wrapper}>
      <h2 className={styles.heading}>{t('heading')}</h2>
      <FilterChips
        selected={filters.selected}
        activeCount={filters.activeCount}
        onRemove={filters.toggle}
        onReset={filters.reset}
      />
      <div className={styles.searchBar}>
        <IconSearch size={16} className={styles.searchIcon} />
        <input
          type="text"
          className={styles.searchInput}
          placeholder={t('searchPlaceholder')}
          value={query}
          onChange={(e) => onSearch(e.target.value)}
        />
      </div>

      <div className={styles.tableScroll}>
        <table className={styles.table}>
          <thead>
            <tr>
              {TABLE_COLUMNS.map((col) => (
                <th key={col.key}>{t(col.labelKey)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((org, i) => (
              <tr key={org.wikidata_url ?? org.domain ?? `${org.org}-${i}`}>
                {TABLE_COLUMNS.map((col) => (
                  <td key={col.key}>{col.render ? col.render(org, t) : col.accessor(org)}</td>
                ))}
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td className={styles.empty} colSpan={TABLE_COLUMNS.length}>
                  {t('noResults')}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className={styles.pagination}>
        <button
          type="button"
          className={styles.navButton}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={currentPage === 1}
        >
          <IconArrowLeft size={16} />
          <span>{t('prevPage')}</span>
        </button>
        {pageItems(currentPage, pageCount).map((item, i) =>
          item === 'ellipsis' ? (
            <span key={`ellipsis-${i}`} className={styles.ellipsis}>
              …
            </span>
          ) : (
            <button
              key={item}
              type="button"
              className={`${styles.pageButton} ${item === currentPage ? styles.pageButtonActive : ''}`}
              onClick={() => setPage(item)}
            >
              {item}
            </button>
          ),
        )}
        <button
          type="button"
          className={`${styles.navButton} ${styles.navButtonNext}`}
          onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
          disabled={currentPage === pageCount}
        >
          <span>{t('nextPage')}</span>
          <IconArrowRight size={16} />
        </button>
      </div>

      <p className={styles.count}>{t('resultCount', { count: filtered.length })}</p>
    </div>
  )
}

export default OrgTable
