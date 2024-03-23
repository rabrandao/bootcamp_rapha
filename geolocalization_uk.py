import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Import postal codes dataframe
df_postcode = pd.read_csv("ONSPD_FEB_2024_UK.csv")
df_postcode = df_postcode[["pcds", "lat", "long"]]

# Load the GeoJSON file
gdf = gpd.read_file("Source_Protection_Zones_Merged.json")
gdf_h = gpd.read_file("Historic_Conservation_Areas.geojson")

# Load the claims spreadsheet data
sinistros_df = pd.read_excel('sinistros.xlsx')

# Create a dictionary to map postal codes to coordinates
postcode_to_coords = df_postcode.set_index('pcds').apply(lambda row: Point(row['long'], row['lat']), axis=1).to_dict()

# Function to search for coordinates based on the postal code
def get_coords_from_postcode(postcode):
    return postcode_to_coords.get(postcode)

# Apply function to add geometry to the claims DataFrame
sinistros_df['geometry'] = sinistros_df['postcode'].apply(get_coords_from_postcode)
sinistros_gdf = gpd.GeoDataFrame(sinistros_df, geometry='geometry')

# Checks if the geometries are valid
sinistros_gdf['is_valid'] = sinistros_gdf['geometry'].apply(lambda geom: geom.is_valid if geom else False)

# Corrects invalid geometries
sinistros_gdf['geometry'] = sinistros_gdf.apply(
    lambda row: row['geometry'].buffer(0) if not row['is_valid'] and row['geometry'] is not None else row['geometry'], 
    axis=1
)

# Run the function to compare the postcode coordinates with GIS files coordinates.
sinistros_gdf['in_source_protection_zone'] = sinistros_gdf.apply(lambda x: gdf.contains(x.geometry).any() if x.geometry else False, axis=1)
sinistros_gdf['in_historic_conservation_area'] = sinistros_gdf.apply(lambda x: gdf_h.contains(x.geometry).any() if x.geometry else False, axis=1)
