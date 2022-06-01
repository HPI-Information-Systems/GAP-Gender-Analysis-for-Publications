import pandas as pd
from sqlite3 import Connection, connect
import streamlit as st
import numpy as np

country_cont = pd.read_csv('countries_continents.csv')
data = pd.read_csv('new_data_2.csv')
conferences = pd.read_csv('sorted_conferences.csv')


def main():
    #conn = connect(DB)
    #init_db(conn)
    #conn.execute("INSERT INTO test (Attribute1, Attribute2) VALUES (42, 'text')")
    #fill_from_json(conn)
    #conn.commit()
    #conn = connect(DB

    st.title('Gender Analysis for Publications')
    st.subheader("No of conference publications per year")
    ps = ''
    option_c, option_Count, option_field = display_relation()

    if st.button('Submit'):
            print (ps, option_c, option_Count, option_field)
            populate_graph (option_c, option_Count, option_field)
    else:
            st.write('Waiting for submission')
    #populate_graph(option[0],option[1],option[2])

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


def populate_graph(conf='', country='', field=''):
    year = np.array(list(range(2000,2022)))
    y = year*0

    ## RETRIEVING OPTIONS AND FILLING UP THE DROP DOWN LISTS TO POPULATE GRAPH
    y_name = 'Y:'
    if(field==[]):
            f1 = (True)
    else:
            f1 = (data['Field'] == field[-1])
            y_name = y_name + field[-1]+'+'
    if(country==[]):
            f2 = (True)
    else:
            f2 = (data['Country'] == country[-1])
            y_name = y_name + country[-1]+'+'
    if(conf==[]):
            f3 = (True)
    else:
            f3 = (data['Conference'] == conf[-1])
            y_name = y_name + conf[-1]+'+'
    try:
            filtered_df = data[f1 & f2 & f3]
    except:
            filtered_df = data
    filtered_df = filtered_df.groupby(filtered_df['Year']).sum()
    if(len(filtered_df)==22):
            y = filtered_df['No of Publications']
    ss = pd.DataFrame({'Year': year, y_name : np.array(y)}).set_index('Year')
    try:
            if (len(ps)!= 0):
                    ps[y_name] = np.array(y)

    except:
            ps = ss
    #ss = ss.rename(columns={'Year':'index'}).set_index('index')
    ## POPULATE GRAPH WITH DATA
    st.line_chart(ps)
    return(ps)


def display_relation():

    ## RETRIEVE OPTIONS
    options_c = tuple(list(conferences['Conference']))
    option_c = st.multiselect('Filter by Conferences:',options_c)

    options_field = tuple(list(conferences['Field'].unique()))
    option_field = st.multiselect('Filter by Field:',options_field)

    options_Count = tuple(list(country_cont['Country']))
    option_Count = st.multiselect('Filter by Country:',options_Count)

    return(option_c, option_Count, option_field)



if __name__ == "__main__":
    main()    
