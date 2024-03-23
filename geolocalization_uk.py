import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Importar dataframe dos códigos postais
df_postcode = pd.read_csv("ONSPD_FEB_2024_UK.csv")
df_postcode = df_postcode[["pcds", "lat", "long"]]

# Carregar o arquivo GeoJSON
gdf = gpd.read_file("Source_Protection_Zones_Merged.json")
gdf_h = gpd.read_file("Historic_Conservation_Areas.geojson")

# Carregar os dados da planilha de sinistros
sinistros_df = pd.read_excel('sinistros.xlsx')

# Criar dicionário para mapear códigos postais para coordenadas
postcode_to_coords = df_postcode.set_index('pcds').apply(lambda row: Point(row['long'], row['lat']), axis=1).to_dict()

# Função para buscar coordenadas com base no código postal
def get_coords_from_postcode(postcode):
    return postcode_to_coords.get(postcode)

# Aplicar função para adicionar geometria ao DataFrame de sinistros
sinistros_df['geometry'] = sinistros_df['postcode'].apply(get_coords_from_postcode)
sinistros_gdf = gpd.GeoDataFrame(sinistros_df, geometry='geometry')

# Verifica se as geometrias são válidas
sinistros_gdf['is_valid'] = sinistros_gdf['geometry'].apply(lambda geom: geom.is_valid if geom else False)

# Corrige as geometrias inválidas
sinistros_gdf['geometry'] = sinistros_gdf.apply(
    lambda row: row['geometry'].buffer(0) if not row['is_valid'] and row['geometry'] is not None else row['geometry'], 
    axis=1
)

# Agora você pode proceder com as verificações em áreas específicas
sinistros_gdf['in_source_protection_zone'] = sinistros_gdf.apply(lambda x: gdf.contains(x.geometry).any() if x.geometry else False, axis=1)
sinistros_gdf['in_historic_conservation_area'] = sinistros_gdf.apply(lambda x: gdf_h.contains(x.geometry).any() if x.geometry else False, axis=1)
