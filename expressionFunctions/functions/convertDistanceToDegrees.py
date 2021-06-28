from qgis.core import *
from qgis.gui import *
import math

@qgsfunction(args='auto', group='Custom')
def convertDistanceToDegrees(distance, lat, long, feature, parent):
    """
    Convert distance.
    <h2>Example usage:</h2>
    <ul>
      <li>Found: convertDistanceToDegrees(5, -8.05389, -34.881111) -> '0.000045'</li>
      <li>Not found: convertDistanceToDegrees(distance, lat, long) -> ''</li>
    </ul>
    """
    referenceSystemOrigin = QgsCoordinateReferenceSystem( 4326 )
    epsgDestination = getSirgarAuthIdByPointLatLong.function(lat, long, feature, parent)
    if not epsgDestination:
        return ''
    referenceSystemDestination = QgsCoordinateReferenceSystem( epsgDestination )

    transformDestination = getGeometryTransforms( referenceSystemOrigin, referenceSystemDestination )
    transformOrigin  = getGeometryTransforms( referenceSystemDestination, referenceSystemOrigin)

    pointA = QgsGeometry().fromPointXY( QgsPointXY(long, lat) )
    pointA.transform( transformDestination )

    pointB = QgsGeometry().fromPointXY( QgsPointXY( pointA.asPoint().x() + distance, pointA.asPoint().y() ) )

    pointA.transform( transformOrigin )
    pointB.transform( transformOrigin )
    return "%f" % pointA.distance( pointB )

def getGeometryTransforms(sourceCrs, destCrs):
    return QgsCoordinateTransform(sourceCrs, destCrs, QgsCoordinateTransformContext())
