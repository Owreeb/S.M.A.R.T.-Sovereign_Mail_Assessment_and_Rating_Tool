import React, { useState } from 'react'

import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import Footer from '@components/landing/Footer'
import Navbar from '@components/landing/Navbar'

import overview from '../../../ABOUT.md?raw'
import datenbasis from '../../../docs/scanner/datenquelle-wikidata.de.md?raw'
import specification from '../../../Souveränitätsindex_V2_Spezifikation.md?raw'
import styles from './About.module.scss'

const tabs = [
  { id: 'overview', label: 'Übersicht', content: overview },
  { id: 'specification', label: 'Souveränitätsindex', content: specification },
  { id: 'datenbasis', label: 'Datenbasis', content: datenbasis },
]

const About = (): React.ReactElement => {
  const [activeTab, setActiveTab] = useState(tabs[0].id)
  const activeContent = tabs.find((tab) => tab.id === activeTab)?.content ?? ''

  return (
    <>
      <Navbar />
      <main className={styles.page}>
        <div className={styles.tabs} role="tablist">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`${styles.tab} ${activeTab === tab.id ? styles.active : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <article className={styles.content}>
          <Markdown remarkPlugins={[remarkGfm]}>{activeContent}</Markdown>
        </article>
      </main>
      <Footer />
    </>
  )
}

export default About
