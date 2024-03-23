import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Importar dataframe dos códigos postais
df_pc = pd.read_csv("ONSPD_FEB_2024_UK.csv")
df_pc = df_pc[["pcds", "lat", "long"]]

# Carregar o arquivo GeoJSON
gdf = gpd.read_file("Source_Protection_Zones_Merged.json")
gdf_hist = gpd.read_file("Historic_Conservation_Areas.geojson")

# Carregar os dados da planilha de sinistros
claims_df = pd.read_excel('sinistros.xlsx')

# Criar dicionário para mapear códigos postais para coordenadas
postcode_to_coords = df_pc.set_index('pcds').apply(lambda row: Point(row['long'], row['lat']), axis=1).to_dict()

# Função para buscar coordenadas com base no código postal
def get_coords_from_postcode(postcode):
    return postcode_to_coords.get(postcode)

# Aplicar função para adicionar geometria ao DataFrame de sinistros
claims_df['geometry'] = claims_df['postcode'].apply(get_coords_from_postcode)
claims_gdf = gpd.GeoDataFrame(claims_df, geometry='geometry')

# Verifica se as geometrias são válidas
claims_gdf['is_valid'] = claims_gdf['geometry'].apply(lambda geom: geom.is_valid if geom else False)

# Corrige as geometrias inválidas
claims_gdf['geometry'] = claims_gdf.apply(
    lambda row: row['geometry'].buffer(0) if not row['is_valid'] and row['geometry'] is not None else row['geometry'], 
    axis=1
)

# Agora você pode proceder com as verificações em áreas específicas
claims_gdf['in_source_protection_zone'] = claims_gdf.apply(lambda x: gdf.contains(x.geometry).any() if x.geometry else False, axis=1)
claims_gdf['in_historic_conservation_area'] = claims_gdf.apply(lambda x: gdf_hist.contains(x.geometry).any() if x.geometry else False, axis=1)
