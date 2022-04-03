import pandas as pd
from sqlite3 import Connection, connect
import streamlit as st


DB = 'gap.db'


def main():
    conn = connect(DB)
    init_db(conn)
    conn.execute("INSERT INTO test (Attribute1, Attribute2) VALUES (42, 'text')")
    conn.commit()

    st.title('Gender Analysis for Publications')
    display_relation('test', conn)


def init_db(conn: Connection):
    # Todo: Outsource to 'database' module
    # Todo: Add create table statements
    conn.execute(
        """CREATE TABLE IF NOT EXISTS test
            (
                Attribute1 INT,
                Attribute2 VARCHAR
            );"""
    )
    conn.commit()


def get_dataframe(conn: Connection, rel: str):
    # Todo: Outsource to 'database' module
    df = pd.read_sql(f"SELECT * from {rel}", con=conn)
    return df


def display_relation(rel: str, conn: Connection):
    # Todo: Outsource to 'frontend' module
    df = get_dataframe(conn, rel)
    st.dataframe(df.head())


if __name__ == "__main__":
    main()    
