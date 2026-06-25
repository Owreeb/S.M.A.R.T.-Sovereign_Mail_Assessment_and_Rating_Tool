export interface StatisticsData {
  overview: Overview
  topMailVendors: Share[]
  topHosters: Share[]
}

export interface Overview {
  orgsScanned: number
  domainsScanned: number
  sovereigntyIndex: number
}

export interface Share {
  name: string
  share: number
}
