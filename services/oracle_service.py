import oracledb

def get_connection():
    return oracledb.connect(
        user="datagatemonitoring",
        password="datagatemonitoring12345",
        dsn="dbdatawhs.diamond.co.id:1521/DBWHS"
    )