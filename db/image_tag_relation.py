
def table_image_tag_relation():
    sql = ("CREATE TABLE IF NOT EXISTS image_tag_relation"
           "("
           "id INTEGER PRIMARY KEY AUTOINCREMENT,"
           "tag_id INTEGER,"
           "image_id INTEGER,"
           "UNIQUE(tag_id, image_id)"
           ");"
           )
