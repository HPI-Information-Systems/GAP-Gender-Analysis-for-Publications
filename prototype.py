import pandas as pd
import datetime
from sqlite3 import Connection, connect
import streamlit as st
import numpy as np
import os
from utils import log

# Connect to SQLite database
conn = connect('gap.db')

# Create cursor object
cursor = conn.cursor()

# function to run query or store output of query


def query_action(sql, action='run'):
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
            store[row[0]] = row[1]
        return(store)

def initViews():
########## STEP 0 #######################
###### Create Indexes for faster querying

    sql = '''CREATE INDEX IF NOT EXISTS publication_author_index
ON PublicationAuthor (PublicationID, Position, DBLPName);'''
    cursor.execute(sql)

    sql = '''CREATE INDEX IF NOT EXISTS author_index
ON Author (AuthorID, Gender, AffiliationID, DBLPName)'''
    cursor.execute(sql)

    sql = '''CREATE INDEX IF NOT EXISTS venue_index ON Venue (VenueID, Name)'''
    cursor.execute(sql)

    sql = '''CREATE INDEX IF NOT EXISTS publication_index
    ON Publication(PublicationID, Year, VenueID)'''
    cursor.execute(sql)

    sql = '''CREATE INDEX IF NOT EXISTS country_index
    ON Country(CountryCode, DisplayName, Continent)'''
    cursor.execute(sql)

    sql = '''CREATE INDEX IF NOT EXISTS affiliation_index
    ON Affiliation(AffiliationID, CountryCode)'''
    cursor.execute(sql)

########## STEP 1 #######################
###### WOMEN authors and their PublicationIDs reunited ######

# Query for INNER JOIN
# Run to update the view in case of a new DBLP dump
# conn.execute(f"DROP VIEW IF EXISTS W_auth_pub;")

    sql = '''SELECT count(name) FROM sqlite_master WHERE type='view' AND name='W_auth_pub';'''
    if(query_action(sql, 'check') != [(1,)]):

        sql = '''CREATE VIEW IF NOT EXISTS W_auth_pub (PublicationID,AuthorID,AffiliationID,Gender,Position)
    AS SELECT PublicationAuthor.PublicationID, AuthorID, AffiliationID, Author.Gender, PublicationAuthor.Position
    FROM Author 
    INNER JOIN PublicationAuthor
    ON Author.DBLPName = PublicationAuthor.DBLPName;'''
        cursor.execute(sql)

########## STEP 2 #######################
###### WOMEN authors, their PublicationIDs, VenueID, Year of publishing reunited ######

# Query for INNER JOIN
# Run to update the view in case of a new DBLP dump
#conn.execute(f"DROP VIEW IF EXISTS W_pub;")

    sql = '''SELECT count(name) FROM sqlite_master WHERE type='view' AND name='W_pub';'''
    if(query_action(sql, 'check') != [(1,)]):

        sql = '''CREATE VIEW IF NOT EXISTS W_pub (PublicationID,AuthorID,Venue, VenueType, AffiliationID,Position, Gender, Year)
        AS SELECT Publication.PublicationID, W_auth_pub.AuthorID, Venue.Name, Venue.Type,  W_auth_pub.AffiliationID, W_auth_pub.Position, W_auth_pub.Gender, Publication.Year
        FROM Publication 
        INNER JOIN W_auth_pub ON W_auth_pub.PublicationID = Publication.PublicationID
        INNER JOIN Venue ON Publication.VenueID = Venue.VenueID;'''

    # sql ='''CREATE TEMPORARY TABLE W_pub (PublicationID, AuthorID, Venue, AFfiliationID, Position, Gender, Year)'''
    # cursor.execute(sql)

    # sql = '''INSERT INTO W_pub
    # SELECT Publication.PublicationID, W_auth_pub.AuthorID, Venue.Name, W_auth_pub.AffiliationID, W_auth_pub.Position, W_auth_pub.Gender, Publication.Year
    # FROM Publication 
    # INNER JOIN W_auth_pub ON W_auth_pub.PublicationID = Publication.PublicationID
    # INNER JOIN Venue ON Publication.VenueID = Venue.VenueID;'''

        cursor.execute(sql)


############### STEP 3 ##########################
# Query for inner-join bewteen Affiliation and Country (ONLY for ones with AffiliationID!=Null)
# Run to update the view in case of a new DBLP dump
#conn.execute(f"DROP VIEW IF EXISTS Pub_place;")

    sql = '''SELECT count(name) FROM sqlite_master WHERE type='view' AND name='Pub_place';'''
    if(query_action(sql, 'check') != [(1,)]):
        sql = '''CREATE VIEW IF NOT EXISTS Pub_place (AffiliationID,Country,Continent)
        AS SELECT AffiliationID, Country.DisplayName, Country.Continent
        FROM Affiliation 
        JOIN Country ON Affiliation.CountryCode = Country.CountryCode;'''
        cursor.execute(sql)
        # W_auth_pub view isnt needed for any future calculations
        conn.execute(f"DROP VIEW IF EXISTS W_auth_pub;")


# reading csv for unique countries and Continents
output1 = pd.merge(pd.read_csv('continents.csv'), pd.read_csv('countries_unique.csv'), on='Code', how='inner')
country_cont = pd.DataFrame(
{'Country': output1['Country'], 'Continent': output1['Continent']})
output1 = None



# creating a placeholder for the fixed sized textbox
# will be used to display additional information about the data like missing affiliations and/or venues
#logtxtbox = st.empty()

# creating session state variables to communicate data between sessions

# if 'logtxt' not in st.session_state:
#    st.session_state.logtxt = ''
# for data comparison across multiple selections
if 'df_compare' not in st.session_state:
    st.session_state.df_compare = pd.DataFrame()
# for column names across multiple selections
if 'y_columns' not in st.session_state:
    st.session_state.y_columns = []
# for min/max of the year range slider
if 'min_max' not in st.session_state:
    sql = '''SELECT min(Year),max(Year) FROM Publication;'''
    st.session_state.min_max = query_action(sql, 'check')[0]
if 'year-range' not in st.session_state:
    st.session_state.year_range = [st.session_state.min_max[0], st.session_state.min_max[1]]
if 'previous-year-range' not in st.session_state:
    st.session_state.previous_year_range = [st.session_state.min_max[0], st.session_state.min_max[1]]

# the main function
def main():
    global logtxt
    st.title('Gender Analysis for Publications')
    initViews()
    display_general_statistics()
    st.subheader("Number of conference publications per year")
    ps = ''
    widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, widget_venue_type, logtxtbox, data_representation = display_relation()
    print(widget_pub_type)
    if st.button('Submit and Compare'):
        # if(compare == True):
        #logtxt = st.session_state.logtxt
        # logtxtbox.write(logtxt)
        populate_graph(
            widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, widget_venue_type, data_representation)

def populate_graph(venue='', country='', cont='', publication_type='', auth_pos='', venue_type='', data_representation=''):

    global cursor
    sql_start = '''SELECT Year, count(PublicationID) as count\nFROM W_pub '''
    # sql_index = '''WITH(INDEX([w_pub_index]))'''
    sql_filter = '''\nWHERE '''
    sql_woman_filter = ''' AND (Gender = "woman")'''
    sql_end = '''\nGROUP BY Year;'''
    sql_cnt_between = '''\nINNER JOIN Pub_place\nON W_pub.AffiliationID == Pub_place.AffiliationID'''

    # the column/fiter names for each selection
    y_name = ''

    # RETRIEVING OPTIONS AND FILLING UP THE DROP DOWN LISTS TO POPULATE GRAPH
    # creating query

    if(venue == []):
        f1 = ''
    else:  # for the 'Venue' of Publication
        f1 = '('
        for v in venue:
            if(v != venue[0]):
                f1 = f1 + ' or '
            f1 = f1 + 'Venue = "' + str(v) + '"'
            y_name = y_name+str(v)+'/'
        f1 = f1 + ')'
    if(country == []):
        f2 = ''
    else:  # for the 'Country' of Author
        f2 = '('
        for c in country:
            if(c != country[0]):
                f2 = f2 + ' or '
            f2 = f2 + 'Pub_place.Country = "' + str(c) + '"'
            y_name = y_name+str(c)+'/'
        f2 = f2 + ')'
    if(cont == []):
        f3 = ''
    else:  # for the 'Continent' of Author
        f3 = '('
        for C in cont:
            if(C != cont[0]):
                f3 = f3 + ' or '
            f3 = f3 + 'Pub_place.Continent = "' + str(C) + '"'
            y_name = y_name+str(C)+'/'
        f3 = f3 + ')'
    if(auth_pos == ''):
        f4 = ''
    else:
        f4 = '('
        if(auth_pos == 'First author'):
            f4 = f4 + 'Position = "1"'
            y_name = y_name + 'First author/'
            # If any author, everyone, including first author
        else:
            f4 = f4 + 'Position = "1" OR Position <> "1"'
            y_name = y_name + 'Any author/'
        f4 = f4 + ')'
    if(publication_type == []):
        f5 = ''
    else:
        f5 = '('
        for p in publication_type:
            if(p != publication_type[0]):
                f5 = f5 + ' or '
            f5 = f5 + 'PublicationType = "' + str(p) + '"'
            y_name = y_name+str(p)+'/'
        f5 = f5 + ')'
    if(venue_type == []):
        f6 = ''
    else:
        f6 = '('
        for vt in venue_type:
            if(vt != venue_type[0]):
                f6 = f6 + ' or '
            f6 = f6 + 'Type = "' + str(vt) + '"'
            y_name = y_name+str(vt)+'/'
        f6 = f6 + ')'
    if(data_representation == 'Relative numbers'):
        show_percentage = True
        y_name = y_name + 'Percentage/'
    else:
        show_percentage = False
        y_name = y_name + 'Absolute/'
    # Dynamically arranging the queries based on input
    sql_logic = [f1, f2, f3, f4, f5, f6]
    newf = ''
    f_count = 0
    for f in sql_logic:
        if(f != ''):
            if(f_count > 0):
                newf = newf + ' AND '
            f_count += 1
            newf = newf + f

    if(y_name not in st.session_state.y_columns):
        # no venue only the other things
        if(f1 == ''):
            sql = sql_start + sql_cnt_between + sql_filter + newf + sql_woman_filter + sql_end
            print(sql)
            out = query_action(sql, 'store')
            if(show_percentage):
                sql = sql_start + sql_cnt_between + sql_filter + newf + sql_end
                print(sql)
                out_all = query_action(sql, 'store')

        # only venue
        elif(f4 == '' and f3 == '' and f2 == '' and f1 != ''):
            sql = sql_start + sql_filter + newf + sql_woman_filter + sql_end
            print(sql)
            out = query_action(sql, 'store')
            if(show_percentage):
                sql = sql_start + sql_filter + newf + sql_end
                out_all = query_action(sql, 'store')
                print(sql)
        # all together
        else:
            sql = sql_start + sql_cnt_between + sql_filter + newf + sql_woman_filter + sql_end
            print(sql)
            out = query_action(sql, 'store')
            if(show_percentage):
                sql = sql_start + sql_cnt_between + sql_filter + newf + sql_end
                print(sql)
                out_all = query_action(sql, 'store')
        

        # Getting data to graph format
        year = pd.array(list(range(int(st.session_state.year_range[0]), int(st.session_state.year_range[1]))))
        y = []

        # TODO: Check if it really outputs the right percentage (e.g. just select Africa, first author, the percentage is very high)
        if(show_percentage):
            for i in year:
                out[i] = out[i]*100/out_all[i]
                try:
                    y.append(out[i])
                except:
                    y.append(0)
        else:
            for Y in year:
                try:
                    y.append(out[Y])
                except:
                    y.append(0)
        y = pd.array(y)

        # construction of line_chart's data

        st.session_state.df_compare[y_name] = y
        st.session_state.y_columns.append(y_name)
    # debugging prints
    # print('st.session_state:')
    # print(st.session_state)
    # print('\n')

        if len(st.session_state.y_columns) > 1:
            line_graph_data = st.session_state.df_compare
            line_graph_data['Year'] = year
            line_graph_data = line_graph_data.set_index('Year')
        else:
            line_graph_data = pd.DataFrame(
                {'Year': year, y_name: y}).set_index('Year')
    else:
        line_graph_data = st.session_state.df_compare
    st.line_chart(line_graph_data)

    # debugging prints
    #print("\nline_graph_data :")
    # print(line_graph_data)
    # return line_graph_data

# the action of clearing all graphs and texts for the reset button


def clear_multi():
    st.session_state.df_compare = pd.DataFrame()
    st.session_state.y_columns = []
    return

# Creates Dynamic queries based on selection and
# runs the query to generate the count to populate the line graphs


def display_general_statistics():
    global cursor

    if 'publication_count' not in st.session_state:
        sql = '''SELECT count(distinct PublicationID) as count\nFROM Publication;'''
        cursor.execute(sql)
        st.session_state.publication_count = cursor.fetchall()[0][0]

    if 'author_count' not in st.session_state:
        sql = '''SELECT count(distinct AuthorID) as count\nFROM Author;'''
        cursor.execute(sql)
        st.session_state.author_count = cursor.fetchall()[0][0]
    if 'affiliation_count' not in st.session_state:
        sql = '''SELECT count(distinct AffiliationID) as count\nFROM Affiliation;'''
        cursor.execute(sql)
        st.session_state.affiliation_count = cursor.fetchall()[0][0]

    if 'venue_count' not in st.session_state:
        sql = '''SELECT count(distinct VenueID) as count\nFROM Venue;'''
        cursor.execute(sql)
        st.session_state.venue_count = cursor.fetchall()[0][0]

    with st.expander('General statistics about the data'):
        col1, col2, col3 = st.columns(3)

        col1.markdown(
            f'**Publications count:** {st.session_state.publication_count}')
        col2.markdown(f'**Author count:** {st.session_state.author_count}')
        col3.markdown(
            f'**Affiliation count:** {st.session_state.affiliation_count}')

        col1.markdown(f'**Venue count:** {st.session_state.venue_count}')
        col2.markdown(f'**Data source:** [dblp](https://dblp.org/)')
        col3.markdown(
            f'**Gender determination:** [GenderAPI](https://gender-api.com/)')

def display_relation():

    global cursor

    if 'filters' not in st.session_state:
        st.session_state.filters = []

    if st.session_state.filters == []:
    # RETRIEVE OPTIONS for DISTINCT Conferences
        sql = '''SELECT DISTINCT(Name) AS Venue FROM Venue;'''
        cursor.execute(sql)

        result = cursor.fetchall()
        options_Venue = []
        for row in result:
            options_Venue.append(row[0])
        options_Venue = tuple(options_Venue)
        st.session_state.filters.append(options_Venue)

        sql = '''SELECT DISTINCT Type FROM Publication;'''
        cursor.execute(sql)
        result = cursor.fetchall()
        options_Type = []
        for row in result:
            options_Type.append(row[0])
        options_Type = tuple(options_Type)
        st.session_state.filters.append(options_Type)

        sql = '''SELECT DISTINCT Type FROM Venue;'''
        cursor.execute(sql)
        result = cursor.fetchall()
        options_Venue_Type = []
        for row in result:
            options_Venue_Type.append(row[0])
        options_Venue_Type = tuple(options_Venue_Type)
        st.session_state.filters.append(options_Venue_Type)

        # RETRIEVE OPTIONS for DISTINCT COUNTRY/CONTINENT
        options_Count = tuple(list(country_cont['Country'].unique()))
        st.session_state.filters.append(options_Count)
        options_Cont = tuple(list(country_cont['Continent'].unique()))
        st.session_state.filters.append(options_Cont)

    # WIDGETs for the drop-down lists for selection
    col1, col2 = st.columns([1, 1])
    with col1:
        widget_cont = st.multiselect(
            'Filter by Continent:', st.session_state.filters[4], key='Cont')
        widget_venue = st.multiselect(
            'Filter by Conference/Journals:', st.session_state.filters[0], key='venue')
        widget_venue_type = st.multiselect('Filter by Venue type:', st.session_state.filters[2], key='venue_type')
        data_representation = st.radio('Data representation (Relative not properly working yet):', ('Absolute numbers', 'Relative numbers'))
    with col2:
        widget_count = st.multiselect(
            'Filter by Country:', st.session_state.filters[3], key='country')
        widget_pub_type = st.multiselect('Filter by publication type:', st.session_state.filters[1], key='publication_type')
        widget_auth_pos = st.radio(
            'Filter by Author Position:', ('First author', 'Any author'), key='author_pos')


    logtxtbox = st.empty()

    # year-raneg selector for the drop-down lists for selection
    st.subheader("Year-range-selector")
    st.session_state.year_range[0], st.session_state.year_range[1] = st.slider("Select years range:",  min_value=st.session_state.min_max[0], value=st.session_state.year_range, max_value=st.session_state.min_max[1])
    # button for clear history

    st.button('Clear History', on_click=clear_multi)
    return(widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, widget_venue_type, logtxtbox, data_representation)


if __name__ == "__main__":
    main()
    # Closing the connection
    conn.close()
