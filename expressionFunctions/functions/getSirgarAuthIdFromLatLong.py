from qgis.core import *
from qgis.gui import *
import math

@qgsfunction(args='auto', group='Custom')
def getSirgarAuthIdByPointLatLong(lat, long, feature, parent):
    """
    Calculates SIRGAS 2000 epsg.
    <h2>Example usage:</h2>
    <ul>
      <li>Found: getSirgarAuthIdByPointLatLong(-8.05389, -34.881111) -> 'ESPG:31985'</li>
      <li>Not found: getSirgarAuthIdByPointLatLong(lat, long) -> ''</li>
    </ul>
    """
    zone_number = math.floor(((long + 180) / 6) % 60) + 1
    if lat >= 0:
        zone_letter = 'N'
    else:
        zone_letter = 'S'
    return getSirgasEpsg('{0}{1}'.format(zone_number, zone_letter))

def getSirgasEpsg(key):
    options = {
        "11N" : "EPSG:31965", 
        "12N" : "EPSG:31966", 
        "13N" : "EPSG:31967", 
        "14N" : "EPSG:31968", 
        "15N" : "EPSG:31969", 
        "16N" : "EPSG:31970", 
        "17N" : "EPSG:31971", 
        "18N" : "EPSG:31972", 
        "19N" : "EPSG:31973", 
        "20N" : "EPSG:31974", 
        "21N" : "EPSG:31975", 
        "22N" : "EPSG:31976", 
        "17S" : "EPSG:31977", 
        "18S" : "EPSG:31978", 
        "19S" : "EPSG:31979", 
        "20S" : "EPSG:31980", 
        "21S" : "EPSG:31981", 
        "22S" : "EPSG:31982", 
        "23S" : "EPSG:31983", 
        "24S" : "EPSG:31984", 
        "25S" : "EPSG:31985"
    }
    return options[key] if key in options else ""