import pytmx

def load_tilemap(file_path):
    tmx_data = pytmx.TiledMap(file_path)
    return tmx_data

file_path = 'map.tmx'  # Replace with the path to your TMX file
tilemap_data = load_tilemap(file_path)

# Accessing tilemap properties
width = tilemap_data.width
height = tilemap_data.height
tilesets = tilemap_data.tilesets

# Accessing individual tilesets
for tileset in tilesets:
    first_gid = tileset.firstgid
    image_source = tileset.image.source
    # You can access other properties of the tileset as needed

    print(f"Tileset GID: {first_gid}")
    print(f"Image Source: {image_source}")

# Accessing tile layers
for layer in tilemap_data.layers:
    if isinstance(layer, pytmx.TiledTileLayer):
        layer_name = layer.name
        layer_data = layer.data
        # You can access other properties of the layer as needed

        print(f"Layer Name: {layer_name}")
        print(f"Layer Data: {layer_data}")

