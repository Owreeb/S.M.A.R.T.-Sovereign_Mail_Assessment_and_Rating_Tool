export interface StatisticsData {
  overview: Overview
  sovereigntyDistribution: SovereigntyDistribution
  topEmailProviders: EmailProvider[]
}

export interface Overview {
  orgsScanned: number
  domainsScanned: number
  sovereigntyIndex: number
  sovereignSystems: number
  hyperscalerRatio: number
}

export interface SovereigntyDistribution {
  sovereign: number
  partially: number
  hyperscaler: number
}

export interface EmailProvider {
  name: string
  share: number
}
