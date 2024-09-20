import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
import multiprocessing as mp
crs = 'EPSG:4326' # WGS84
raw_data_path = './data/census/geojson'
raw_data_path = Path(raw_data_path)
raw_data_list = list(raw_data_path.rglob('*.geojson'))
def join_gdf(df_gdf, filename):
    gdf = gpd.read_file(filename)
    gdf = gdf.to_crs(crs)  # Convert to WGS84 CRS
    gdf.set_index('FIPSWITHTRACT', inplace=True)
    join_result = gpd.sjoin(df_gdf, gdf, how='inner')  # Spatial join to match points to polygons
    return join_result
def create_point(row):
    return Point(row['sims_longitude'], row['sims_latitude'])
df = pd.read_stata(r'./data/branch_list 2.dta')
df['geometry'] = df.apply(create_point, axis=1)  # Create geometry column from lat/lon
df_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=crs)  # Convert to GeoDataFrame with WGS84 CRS


join_result_list = []
# for filename in raw_data_list:
#     join_result_list.append(join_gdf(df_gdf, filename))
def process_file(filename):
    return join_gdf(df_gdf, filename)

with mp.Pool(mp.cpu_count()) as pool:
    join_result_list = pool.map(process_file, raw_data_list)

result_gdf = pd.concat(join_result_list)
result_gdf.to_file(r'./data/branch_list_geo_dta.geojson',driver='GeoJSON')
result_gdf = result_gdf.drop_duplicates(subset=['namefull', 'addresbr'],keep='last')
result_gdf.to_crs(crs=crs)
result_gdf.to_file(r'./data/branch_list_geo_dta_without_duplicate.geojson',driver='GeoJSON')