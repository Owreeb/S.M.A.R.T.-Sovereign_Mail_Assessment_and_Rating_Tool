const mail = {
  roles: {
    smtp_in: 'Inbound',
    imap_pop3: 'Mailbox',
    smtp_out: 'Outbound',
    webmailer: 'Webmail',
  },
  catPublic: 'Public sector',
  catEuVendor: 'EU vendor',
  catEuSub: 'EU subsidiary',
  catIntl: 'International',
  catHyperscaler: 'US hyperscaler',
  catUnknown: 'Unknown',
  unidentified: 'Unidentified server',
  hosting: 'Hosting',
  hostingUnknown: 'Unknown',
  via: 'via {{name}}',
}

export default mail
