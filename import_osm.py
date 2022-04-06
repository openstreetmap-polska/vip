import requests
import pandas as pd
import geopandas as gpd


from IPython.core.display import HTML

# parametry
OVERPASS_INT_URL = 'https://overpass.kumi.systems/api/interpreter'

# zapytanie do osm
overpass_query = """
    [out:json][timeout:1000];area(id:3600224457)->.ds;
    (
    nw["indoormark"="beacon"](area.searchArea);
    nw["traffic_signals:sound"](area.searchArea);
    );
    out center;
    """

# generowanie zapytania do overpassa
response = requests.get(OVERPASS_INT_URL, params = {'data': overpass_query})
if response.ok:
  data = response.json()
  print('Dane pobrane!')
else:
  display(HTML(response.text))


# standaryzowanie danych
df = pd.json_normalize(data['elements'])
df['lat'].fillna(df['center.lat'], inplace=True)
df['lon'].fillna(df['center.lon'], inplace=True)
df.columns = df.columns.str.replace("tags.","")
df.drop(['nodes', 'center.lat', 'center.lon','phone '], axis=1, inplace=True, errors='ignore')
df.columns.drop(list(df.filter(regex='payment:')))
print('Dane zestandaryzowane')


# tworzenie geojson
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat))
gdf.to_file("out.geojson", driver='GeoJSON')

