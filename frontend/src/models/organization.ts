export type SovereigntyLevel = 'low' | 'medium' | 'high'

export type ProviderType = 'hyperscaler' | 'national' | 'regional' | 'self-hosted'

export interface Organization {
  org: string
  domain: string
  category: string
  lat: number
  long: number
  provider: string[]
  smtp_software: string[]
  last_checked: string

  sovereignty_index: number
  sovereignty_level: SovereigntyLevel
  provider_type: ProviderType
  provider_location: [number, number]
  provider_country: string
}
