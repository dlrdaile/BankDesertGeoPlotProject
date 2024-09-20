import multiprocessing as mp
from pathlib import Path
import geopandas as gpd
import pandas as pd
crs = 'EPSG:4326' # WGS84
# Load the shapefile with census tracts
USA_COUNTRY_MAP_DF = pd.read_csv(r'./USA_COUNTY.csv',dtype=str)
USA_COUNTRY_MAP_DF['COMBINED_ID'] = USA_COUNTRY_MAP_DF['STATE'] + USA_COUNTRY_MAP_DF['COUNTY']
USA_COUNTRY_MAP_DF.set_index('COMBINED_ID',inplace=True)

raw_data_path = './data/census'
raw_data_path = Path(raw_data_path)
raw_data_list = list(raw_data_path.rglob('*.zip'))
savee_dir = './data/census/geojson'
savee_dir = Path(savee_dir)
savee_dir.mkdir(parents=True, exist_ok=True)

def process_geo_data(filename,saved_filename):
    gdf = gpd.read_file(filename)
    gdf['FIPSWITHTRACT'] = gdf['STATEFP10'] + gdf['COUNTYFP10'] + gdf['TRACTCE10']
    join_data_gdf = gdf.groupby('FIPSWITHTRACT').agg({'geometry':lambda x: x.union_all()}).reset_index()
    join_data_gdf['FIPS'] = join_data_gdf['FIPSWITHTRACT'].str[:5]
    join_data_gdf['TRACTCE10'] = join_data_gdf['FIPSWITHTRACT'].str[5:]
    join_data_gdf['STATEFP10'] = join_data_gdf['FIPS'].str[:2]
    join_data_gdf['COUNTYFP10'] = join_data_gdf['FIPS'].str[2:]
    join_data_gdf['STATE_NAME'] = join_data_gdf['FIPS'].map(USA_COUNTRY_MAP_DF['STATE_NAME'])
    join_data_gdf['COUNTY_NAME'] = join_data_gdf['FIPS'].map(USA_COUNTRY_MAP_DF['COUNTY_NAME'])
    gdf = gpd.GeoDataFrame(join_data_gdf, geometry='geometry', crs=crs)  # Convert to GeoDataFrame with WGS84 CRS
    gdf.set_index('FIPSWITHTRACT', inplace=True)
    print(f"Geo data processed from {filename}")
    gdf.to_file(saved_filename, driver='GeoJSON')
    print(f"Geo data saved to {saved_filename}")

def process_file(raw_data):
    saved_filename = raw_data.name.replace('.zip', '.geojson')
    saved_filename = savee_dir / saved_filename
    if saved_filename.exists():
        print(f"File {saved_filename} already exists")
        return
    process_geo_data(raw_data, saved_filename)
if __name__ == '__main__':
    # 创建一个进程池
    pool = mp.Pool(mp.cpu_count())

    # 使用进程池并行处理文件
    pool.map(process_file, raw_data_list)

    # 关闭进程池并等待所有进程完成
    pool.close()
    pool.join()