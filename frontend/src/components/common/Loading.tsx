import React from 'react'

import styles from './Loading.module.scss'

const Loading = (): React.ReactElement => (
  <div className={styles.wrapper} role="status" aria-label="Loading">
    <div className={styles.spinner} />
  </div>
)

export default Loading
