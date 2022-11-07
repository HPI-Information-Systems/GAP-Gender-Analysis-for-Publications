import pandas as pd
from sqlite3 import Connection, connect


csv = pd.read_csv("filters\Venues.csv")

print(csv[0])
sql = """
 SELECT
    CASE WHEN EXISTS
    (
        SELECT * FROM AllTogether
        WHERE Venue = """
