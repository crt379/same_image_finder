
def create_table_image_tag():
    sql = ("CREATE TABLE IF NOT EXISTS image_tag"
           "("
           "id INTEGER PRIMARY KEY AUTOINCREMENT,"
           "tag INTEGER UNIQUE"
           ");"
           )