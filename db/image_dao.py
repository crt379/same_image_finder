from sqlite3 import Connection
from typing import Any, List


class ImageDao:

    def __init__(self, connect: Connection) -> None:
        self.connect = connect

    def create(self) -> None:
        sql = (
            "CREATE TABLE IF NOT EXISTS image"
            "("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "md5 VARCHAR(100) UNIQUE,"
            "data ARRAY"
            ")"
        )
        self.connect.execute(sql)

    def insert(self, md5: str, image) -> None:
        sql = (
            "INSERT INTO image "
            "(md5, data) "
            "VALUES (?, ?)"
        )
        self.connect.execute(sql, (md5, image))
        self.connect.commit()

    def select(self, /, md5: str = None) -> List[Any]:
        sql = (
            "SELECT * "
            "FROM image "
        )

        wheres = []
        parameters = []
        if md5 is not None:
            wheres.append("md5=?")
            parameters.append(md5)

        if len(wheres) > 0:
            sql += f"WHERE {', '.join(wheres)}"

        return self.connect.execute(sql, parameters).fetchall()


if __name__ == "__main__":
    from conn import sift_db_connect

    conn = sift_db_connect()
    image_dao = ImageDao(conn)
    image_dao.create()
    r = image_dao.select(md5="dddddd")
    print(r)
