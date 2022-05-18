import pandas as pd
from sqlite3 import Connection, connect
import streamlit as st
import numpy as np

DB = 'test.db'


def main():
    #conn = connect(DB)
    #init_db(conn)
    #conn.execute("INSERT INTO test (Attribute1, Attribute2) VALUES (42, 'text')")
    #fill_from_json(conn)
    #conn.commit()
    #conn = connect(DB)
    st.title('Gender Analysis for Publications')
    st.subheader("No of Articles by year journal")
    option = display_relation()
    populate_graph(option)

def fill_from_json(conn: Connection):
    df = pd.read_json('article_002.json')
    df = df.iloc[3:,[2,8]]
    for x,d in df.iterrows():
        conn.execute("""INSERT INTO test (YEAR, JOURNAL) VALUES (?,?)""",(d['year'][0], d['journal'][0]))
        conn.commit()
    conn.close()
    

def init_db(conn: Connection):
    # Todo: Outsource to 'database' module
    # Todo: Add create table statements
    conn.execute(
        """CREATE TABLE IF NOT EXISTS test
            (
                YEAR INT,
                JOURNAL TEXT
            );"""
    )
    conn.commit()


def get_options(conn: Connection):
    # Todo: Outsource to 'database' module
    sql1 = """SELECT DISTINCT JOURNAL FROM test;"""
    options = pd.read_sql(sql1, conn)
    optionl = list()
    for d in data.values:
        optionl.append(d[0])
    sql2 = """SELECT * FROM test WHERE JOURNAL =="""
    return (tuple(optionl),sql2)


def populate_graph(option):

    ## RETRIEVING OPTIONS AND FILLING UP THE DROP DOWN LISTS TO POPULATE GRAPH
    ss = pd.DataFrame({})
    with open('1.txt') as f:
        one = f.readlines()
    with open('2.txt') as f:
        two = f.readlines()
    with open('3.txt') as f:
        three = f.readlines()
    with open('year.txt') as f:
        year = f.readlines()

    one = [int(x[:-1]) for x in one]
    two = [int(x[:-1]) for x in two]
    three = [int(x[:-1]) for x in three]
    for ii in range(0,3):

        if(ii == 0):
        	ss1 = pd.DataFrame({'year': np.array(year), 'one' : np.array(one)})
        	ss1 = ss1.rename(columns={'year':'index'}).set_index('index')
        elif(ii == 1):
        	ss2 = pd.DataFrame({'year': np.array(year), 'two' : np.array(two)})
        	ss2 = ss2.rename(columns={'year':'index'}).set_index('index')
        elif(ii == 2):
        	ss3 = pd.DataFrame({'year': np.array(year), 'three' : np.array(three)})
        	ss3 = ss3.rename(columns={'year':'index'}).set_index('index')


    count = 0
    for op in option:

        if(op == 'one'):
        	if(count == 0):
        		ss = ss1
        	else:
        		ss['one'] = one
        elif(op == 'two'):
        	if(count == 0):
        		ss = ss2
        	else:
        		ss['two'] = two
        elif(op == 'three'):
        	if(count == 0):
        		ss = ss3
        	else:
        		ss['three'] = three
        count = count + 1
	

    ## POPULATE GRAPH WITH DATA
    st.line_chart(ss)


def display_relation():
    # Todo: Outsource to 'frontend' module
    #options,sql2 = get_options(conn)
    #with open('temp_journal.txt') as f:
    #    options = f.readlines()



    ## RETRIEVE OPTIONS
    options = ('one','two','three')
    option = st.multiselect('by which Journal would you like to filter by:',options)
    st.write('Your selected Journals:', option)

    return (option)


if __name__ == "__main__":
    main()    
