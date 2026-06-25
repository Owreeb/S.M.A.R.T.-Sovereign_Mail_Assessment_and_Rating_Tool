export type SovereigntyLevel = 'sehr-hoch' | 'hoch' | 'mittel' | 'niedrig' | 'sehr-niedrig' | 'unbekannt'

export type MailSystemRole = 'smtp_out' | 'smtp_in' | 'imap_pop3' | 'webmailer'

export interface MailSystem {
  software: string | null
  vendor: string | null
  vendor_country: string | null
  vendor_country_rating: number | null
  vendor_category: string | null
  vendor_category_rating: number | null
  open_source_rating: number | null
  countries: string[]
  hosters: string[]
  proxy: MailSystem | null
}

export type MailSystems = Record<MailSystemRole, MailSystem[]>

export interface Organization {
  org: string
  domain: string | null
  email_domain: string | null
  category: string
  wikidata_url: string | null
  city: string | null
  state: string | null
  country: string | null
  lat: number | null
  long: number | null
  last_checked: string | null

  // Souveränitätsindex V2: 1 = most sovereign ... 6 = least sovereign, null = not rated.
  sovereignty_index: number | null
  providers: string[]
  hosters: string[]
  mail_systems: MailSystems
}

// An organization that has coordinates and can be placed on the map.
export type MappableOrganization = Organization & { lat: number; long: number }
