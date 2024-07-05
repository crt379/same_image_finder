from sqlite3 import Connection
from typing import Any, List


class SiftDao:

    __table_name = "sift"

    def __init__(self, connect: Connection) -> None:
        self.connect = connect

    def create(self) -> None:
        sql = (
            f"CREATE TABLE IF NOT EXISTS {self.__table_name}"
            "("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "image_md5 VARCHAR(100) UNIQUE, "
            "des ARRAY"
            ");"
        )
        self.connect.execute(sql)

    def insert(self, image_md5: str, des) -> None:
        sql = (
            f"INSERT INTO {self.__table_name} "
            "(image_md5, des) "
            "VALUES (?, ?) "
        )
        self.connect.execute(sql, (image_md5, des))
        self.connect.commit()

    def select(self, image_md5: str = None) -> List[Any]:
        sql = (
            "SELECT * "
            f"FROM {self.__table_name} "
        )

        wheres = []
        parameters = []
        if image_md5 is not None:
            wheres.append("image_md5=?")
            parameters.append(image_md5)

        if len(wheres) > 0:
            sql += f"WHERE {', '.join(wheres)}"

        return self.connect.execute(sql, parameters).fetchall()