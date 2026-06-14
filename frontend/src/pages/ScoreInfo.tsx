import React from 'react'

import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import Footer from '@components/landing/Footer'
import Navbar from '@components/landing/Navbar'

import specification from '../../../Souveränitätsindex_V2_Spezifikation.md?raw'
import styles from './ScoreInfo.module.scss'

const ScoreInfo = (): React.ReactElement => {
  return (
    <>
      <Navbar />
      <main className={styles.page}>
        <article className={styles.content}>
          <Markdown remarkPlugins={[remarkGfm]}>{specification}</Markdown>
        </article>
      </main>
      <Footer />
    </>
  )
}

export default ScoreInfo
