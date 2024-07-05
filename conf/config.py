import toml

default_config = {
    "threads": {
        "max": 4,
    },
    "image": {
        "image_suffixs": ['.xbm', '.tif', '.pjp', '.svgz', '.jpg', '.jpeg', '.ico', '.tiff', 
                          '.gif', '.svg', '.jfif', '.webp', '.png', '.bmp', '.pjpeg', '.avif'],
    }
}

config = default_config

try:
    load_config = toml.load('config.toml')
    config.update(load_config)
except Exception as e:
    print(e)
