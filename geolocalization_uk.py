import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Import postal codes dataframe
df_pc = pd.read_csv("ONSPD_FEB_2024_UK.csv")
df_pc = df_pc[["pcds", "lat", "long"]]

# Load the GeoJSON file
gdf = gpd.read_file("Source_Protection_Zones_Merged.json")
gdf_hist = gpd.read_file("Historic_Conservation_Areas.geojson")

# Load the claims spreadsheet data
claims_df = pd.read_excel('sinistros.xlsx')

# Create a dictionary to map postal codes to coordinates
postcode_to_coords = df_pc.set_index('pcds').apply(lambda row: Point(row['long'], row['lat']), axis=1).to_dict()

# Function to search for coordinates based on the postal code
def get_coords_from_postcode(postcode):
    return postcode_to_coords.get(postcode)

# Apply function to add geometry to the claims DataFrame
claims_df['geometry'] = claims_df['postcode'].apply(get_coords_from_postcode)
claims_gdf = gpd.GeoDataFrame(claims_df, geometry='geometry')

# Checks if the geometries are valid
claims_gdf['is_valid'] = claims_gdf['geometry'].apply(lambda geom: geom.is_valid if geom else False)

# Corrects invalid geometries
claims_gdf['geometry'] = claims_gdf.apply(
    lambda row: row['geometry'].buffer(0) if not row['is_valid'] and row['geometry'] is not None else row['geometry'], 
    axis=1
)

# Run the function to compare the postcode coordinates with GIS files coordinates.
claims_gdf['in_source_protection_zone'] = claims_gdf.apply(lambda x: gdf.contains(x.geometry).any() if x.geometry else False, axis=1)
claims_gdf['in_historic_conservation_area'] = claims_gdf.apply(lambda x: gdf_hist.contains(x.geometry).any() if x.geometry else False, axis=1)
