import geojson

def convert_to_geojson(data, lat_attr='latitude', lon_attr='longitude', properties=None):
    features = []
    for item in data:
        point = geojson.Point((getattr(item, lon_attr), getattr(item, lat_attr)))
        feature_properties = {prop: getattr(item, prop) for prop in properties} if properties else {}
        feature = geojson.Feature(geometry=point, properties=feature_properties)
        features.append(feature)
    return geojson.FeatureCollection(features)