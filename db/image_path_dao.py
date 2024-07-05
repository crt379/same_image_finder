from sqlite3 import Connection
from typing import Any, List

class ImagePathDao:

    def __init__(self, connect: Connection) -> None:
        self.connect = connect

    def create(self) -> None:
        sql = (
            "CREATE TABLE IF NOT EXISTS image_path"
            "("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "path VARCHAR(4096) UNIQUE,"
            "md5 VARCHAR(100) NOT NULL"
            ")"
        )
        self.connect.execute(sql)

    def insert(self, path: str, md5: str) -> None:
        sql = (
            "INSERT INTO image_path "
            "(path, md5) "
            "VALUES (?, ?)"
        )
        self.connect.execute(sql, (path, md5))
        self.connect.commit()

    def select(self, /, path: str = None, md5: str = None) -> List[Any]:
        sql = (
            "SELECT * "
            "FROM image_path "
        )

        wheres = []
        parameters = []
        if path is not None:
            wheres.append("path=?")
            parameters.append(path)

        if md5 is not None:
            wheres.append("md5=?")
            parameters.append(md5)

        if len(wheres) > 0:
            sql += f"WHERE {', '.join(wheres)}"

        return self.connect.execute(sql, parameters).fetchall()
    
    def update(self, path: str, md5: str) -> None:
        sql = (
            "UPDATE image_path "
            "SET md5 = ? "
            "WHERE path = ? "
        )

        self.connect.execute(sql, (md5, path))
        self.connect.commit()