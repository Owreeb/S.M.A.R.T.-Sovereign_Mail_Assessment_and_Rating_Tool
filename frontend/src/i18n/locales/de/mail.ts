const mail: typeof import('../en/mail').default = {
  roles: {
    smtp_in: 'Eingang',
    imap_pop3: 'Postfach',
    smtp_out: 'Ausgang',
    webmailer: 'Webmail',
  },
  catPublic: 'Öffentlich',
  catEuVendor: 'EU-Anbieter',
  catEuSub: 'EU-Tochter',
  catIntl: 'International',
  catHyperscaler: 'US-Hyperscaler',
  catUnknown: 'Unbekannt',
  unidentified: 'Unbekannter Server',
  hosting: 'Hosting',
  hostingUnknown: 'Unbekannt',
  via: 'über {{name}}',
}

export default mail
