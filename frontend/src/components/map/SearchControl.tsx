import { useEffect } from 'react'

import { GeoSearchControl, OpenStreetMapProvider } from 'leaflet-geosearch'
import { useTranslation } from 'react-i18next'
import { useMap } from 'react-leaflet'

const SearchControl = (): null => {
  const map = useMap()
  const { t } = useTranslation('map')

  useEffect(() => {
    const provider = new OpenStreetMapProvider()
    const searchControl = GeoSearchControl({
      provider,
      style: 'bar',
      autoClose: true,
      retainZoomLevel: false,
      showMarker: false,
      searchLabel: t('searchLabel'),
      keepResult: false,
    })

    map.addControl(searchControl)

    return () => {
      map.removeControl(searchControl)
    }
  }, [map, t])

  return null
}

export default SearchControl
