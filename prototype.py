import pandas as pd
from sqlite3 import Connection, connect
import streamlit as st
import numpy as np
import os

# Connect to SQLite database
conn = connect('gap.db')
  
# Create cursor object
cursor = conn.cursor()

## function to run query or store output of query
def query_action(sql,action='run'):
    global cursor
    # Executing the query
    cursor.execute(sql)
    if (action != 'run'):
            store = {}
            # Fetching rows from the result table
            result = cursor.fetchall()
            if(action == 'check'):
                    return result
            for row in result:
                    store[row[0]]= row[1]
            return(store)


########## STEP 1 #######################
###### WOMEN authors and their PublicationIDs reunited ######

# Query for INNER JOIN
# connection.execute(f"DROP VIEW IF EXISTS W_auth_pub;")

sql = '''SELECT count(name) FROM sqlite_master WHERE type='view' AND name='W_auth_pub';'''
if(query_action(sql,'check') != [(1,)]):
    sql = '''CREATE VIEW W_auth_pub (PublicationID,AuthorID,AffiliationID,Gender,Position)
    AS SELECT PublicationAuthor.PublicationID, AuthorID, AffiliationID, Author.Gender, PublicationAuthor.Position
    FROM Author 
    INNER JOIN PublicationAuthor
    ON Author.DBLPName = PublicationAuthor.DBLPName
    WHERE Author.Gender='woman';'''
    cursor.execute(sql)

########## STEP 2 #######################
###### WOMEN authors, their PublicationIDs, VenueID, Year of publishing reunited ######

# Query for INNER JOIN
#connection.execute(f"DROP VIEW IF EXISTS W_pub;")

sql = '''SELECT count(name) FROM sqlite_master WHERE type='view' AND name='W_pub';'''
if(query_action(sql,'check') != [(1,)]):
    sql = '''CREATE VIEW W_pub (PublicationID,AuthorID,Venue,AffiliationID,Position,Year)
    AS SELECT Publication.PublicationID, W_auth_pub.AuthorID, Venue.Name, W_auth_pub.AffiliationID,     W_auth_pub.Position, Publication.Year
    FROM Publication 
    INNER JOIN W_auth_pub ON W_auth_pub.PublicationID = Publication.PublicationID
    INNER JOIN Venue ON Publication.VenueID = Venue.VenueID;'''
    cursor.execute(sql)


############### STEP 3 ##########################
# Query for inner-join bewteen Affiliation and Country (ONLY for ones with AffiliationID!=Null)
#conn.execute(f"DROP VIEW IF EXISTS Pub_place;")

sql = '''SELECT count(name) FROM sqlite_master WHERE type='view' AND name='Pub_place';'''
if(query_action(sql,'check') != [(1,)]):
    sql = '''CREATE VIEW Pub_place (AffiliationID,Country,Continent)
    AS SELECT AffiliationID, Country.DisplayName, Country.Continent
    FROM Affiliation 
    JOIN Country ON Affiliation.CountryCode = Country.CountryCode;'''

    cursor.execute(sql)
    connection.execute(f"DROP VIEW IF EXISTS W_pub;")


# reading csv for unique countries and Continents
output1 = pd.merge(pd.read_csv('continents.csv'), pd.read_csv('countries_unique.csv'),on='Code',how='inner')
country_cont = pd.DataFrame({'Country': output1['Country'], 'Continent' : output1['Continent']})
output1 = None

# creating a placeholder for the fixed sized textbox
logtxtbox = st.empty()

# creating session state variables to communicate between sessions
if 'logtxt' not in st.session_state:
    st.session_state.logtxt = ''
prev_compare = False
if 'df_compare' not in st.session_state:
    st.session_state.df_compare = pd.DataFrame()
if 'y_columns' not in st.session_state:
    st.session_state.y_columns = []
year = pd.array(list(range(2000,2022)))

if 'compare' not in st.session_state:
    st.session_state.compare = False


## the main function
def main():

    global logtxt
    st.title('Gender Analysis for Publications')
    st.subheader("No of conference publications per year")
    ps = ''
    widget_venue, widget_count, widget_cont,logtxtbox,start_year,end_year = display_relation()
    if st.button('Submit and Compare'):
            #if(compare == True):
            logtxt = st.session_state.logtxt
            logtxtbox.write(logtxt)
            populate_graph (widget_venue, widget_count, widget_cont,start_year,end_year)

## Session state management
## the action of clearing all graphs and texts for the reset button
def clear_multi():
    st.session_state.conf = []
    st.session_state.country = []
    st.session_state.field = []
    st.session_state.df_compare = pd.DataFrame()
    st.session_state.logtxt = ''
    st.session_state.y_columns = []
    return


def populate_graph(venue='', country='', cont='', start_year='2000', end_year='2022' ,compare = False):

    global cursor
    sql_start = '''SELECT Year, count(PublicationID) as count\nFROM W_pub '''
    sql_filter = '''\nWHERE '''
    sql_end = '''\nGROUP BY Year;'''
    sql_cnt_between = '''\nINNER JOIN Pub_place\nON W_pub.AffiliationID == Pub_place.AffiliationID'''

    ## take the slider input for year filter
    y_name = ''

    ## RETRIEVING OPTIONS AND FILLING UP THE DROP DOWN LISTS TO POPULATE GRAPH
    ## creating query
    if(venue==[]):
            f1 = ''
    else:   ## for the 'Venue' of Publication
            f1 = '('
            for v in venue:
                    if(v!=venue[0]):
                            f1 = f1 + ' or '
                    f1 = f1 + 'Venue = "' + str(v) + '"'
                    y_name = y_name+str(v)+'/'
            f1 = f1 + ')'
    if(country==[]):
            f2 = ''
    else:   ## for the 'Country' of Author
            f2 = '('
            for c in country:
                    if(c!=country[0]):
                            f2 = f2 + ' or '
                    f2 = f2 + 'Pub_place.Country = "' + str(c) + '"'
                    y_name = y_name+str(c)+'/'
            f2 = f2 + ')'
    if(cont==[]):
            f3 = ''
    else:   ## for the 'Continent' of Author
            f3 = '('
            for C in cont:
                    if(C!=cont[0]):
                            f3 = f3 + ' or '
                    f3 = f3 + 'Pub_place.Continent = "' + str(C) + '"'
                    y_name = y_name+str(C)+'/'
            f3 = f3 + ')'


    ## Dynamically arranging the queries based on input
    sql_logic = [f1,f2,f3]
    newf = ''
    f_count = 0
    for f in sql_logic:
            if(f!=''):
                    if(f_count >0):
                            newf = newf + ' AND '
                    f_count +=1
                    newf = newf + f

    ## all empty option, that is the full graph
    if(f_count == 0):
            y_name = 'All Data'
            sql = sql_start + sql_end
            out = query_action(sql,'store')
    ## no venue only the countries/continents
    elif(f1==''):
            sql = sql_start + sql_cnt_between + sql_filter + newf + sql_end
            out = query_action(sql,'store')
    ## only venue
    elif(f3=='' and f2=='' and f1!=''):
            sql = sql_start + sql_filter + newf + sql_end
            out = query_action(sql,'store')
    ## all together
    else:
            sql = sql_start + sql_cnt_between + sql_filter + newf + sql_end
            out = query_action(sql,'store')
    ## Print generated SQL query
    print(sql+'\n')
    
    ## Getting data to graph format
    year = pd.array(list(range(int(start_year),int(end_year))))
    y = []
    for Y in year:
            try: 
                    y.append(out[Y])
            except: 
                    y.append(0)
    y = pd.array(y)
    ## construction of st.line_chart's data
    ## Session state management
    st.session_state.df_compare[y_name] = y
    st.session_state.y_columns.append(y_name)
    
    ##debugging outputs
    # print('st.session_state:')
    # print(st.session_state)
    # print('\n')
    if len(st.session_state.y_columns)>1:
            line_graph_data = st.session_state.df_compare
            line_graph_data['Year'] = year
            line_graph_data = line_graph_data.set_index('Year')
    else:
            line_graph_data = pd.DataFrame({'Year': year, y_name : y}).set_index('Year')
    ## debugging prints
    # print("\nline_graph_data :")
    # print(line_graph_data)
    st.line_chart(line_graph_data)



def display_relation():

    global cursor
    ## RETRIEVE OPTIONS for DISTINCT Conferences
    sql = '''SELECT DISTINCT(Name) AS Venue FROM Venue;'''
    cursor.execute(sql)

    result = cursor.fetchall()
    options_Venue = []
    for row in result:
           options_Venue.append(row[0])
    options_Venue = tuple(options_Venue)

    ## RETRIEVE OPTIONS for DISTINCT COUNTRY/CONTINENT
    options_Count = tuple(list(country_cont['Country'].unique()))    
    options_Cont = tuple(list(country_cont['Continent'].unique()))

    ## WIDGETs for the drop-down lists for selection
    widget_cont, widget_count = st.columns([1,1])
    with widget_cont:
           widget_cont = st.multiselect('Filter by Continent:',options_Cont,key='Cont')
    with widget_count:
           widget_count = st.multiselect('Filter by Country:',options_Count,key='country')

    widget_venue = st.multiselect('Filter by Conference/Journals:',options_Venue,key='venue')

    logtxtbox = st.empty()

    ## year-raneg selector for the drop-down lists for selection
    yearmax = pd.array(list(range(1930,2022)))

    st.subheader("Year-range-selector")
    start_year,end_year = st.slider("Year span:",  min_value = 1900,value=[2000,2022],max_value=2030)
    ## button for clear history
    st.button('Clear History', on_click=clear_multi)
    return(widget_venue, widget_count, widget_cont,logtxtbox,start_year,end_year)



if __name__ == "__main__":
    main()
    # Closing the connection
    conn.close()
