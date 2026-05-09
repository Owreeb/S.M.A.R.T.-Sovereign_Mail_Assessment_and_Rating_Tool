import { useEffect } from 'react'

import { GeoSearchControl, OpenStreetMapProvider } from 'leaflet-geosearch'
import { useMap } from 'react-leaflet'

const SearchControl = (): null => {
  const map = useMap()

  useEffect(() => {
    const provider = new OpenStreetMapProvider()
    const searchControl = GeoSearchControl({
      provider,
      style: 'bar',
      autoClose: true,
      retainZoomLevel: false,
      showMarker: false,
      searchLabel: 'Stadt oder Adresse suchen',
      keepResult: false,
    })

    map.addControl(searchControl)

    return () => {
      map.removeControl(searchControl)
    }
  }, [map])

  return null
}

export default SearchControl
