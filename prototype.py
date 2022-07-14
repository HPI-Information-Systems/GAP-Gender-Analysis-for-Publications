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


def main():
    global logtxt
    st.title('Gender Analysis for Publications')

    if 'df_compare' not in st.session_state:
        st.session_state.df_compare = pd.DataFrame()
    if 'y_columns' not in st.session_state:
        st.session_state.y_columns = []
    if 'min_max' not in st.session_state:
        sql = '''SELECT min(Year),max(Year) FROM AllTogether;'''
        st.session_state.min_max = query_action(sql, 'check')[0]
    if 'year_range' not in st.session_state:
        st.session_state.year_range = [
            st.session_state.min_max[0], st.session_state.min_max[1]]
    if 'previous_year_range' not in st.session_state:
        st.session_state.previous_year_range = [
            st.session_state.min_max[0], st.session_state.min_max[1]]

    display_general_statistics()
    st.subheader("Number of conference publications per year")
    widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, logtxtbox, data_representation = display_filters()
    if st.button('Submit and Compare'):
        populate_graph(
            widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, data_representation)
    display_graph_checkboxes()

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

# Generate the checkboxes for the graphs to be displayed
def display_graph_checkboxes():
    st.subheader('Graph history')
    if len(st.session_state.y_columns) == 0:
        st.markdown('You have not generated any graphs yet')
    else:
        st.session_state.y_columns.sort(key=lambda x: x[1], reverse=True)
        for i in range(len(st.session_state.y_columns)):
            globals()['graph_checkbox_%s' % i] = st.checkbox(
                st.session_state.y_columns[i][0], value=st.session_state.y_columns[i][1], key=i)
            if globals()['graph_checkbox_%s' % i]:
                st.session_state.y_columns[i][1] = True
                log(str(st.session_state.y_columns[i][0]) +
                    str(st.session_state.y_columns[i][1]))
            else:
                st.session_state.y_columns[i][1] = False
                log(str(st.session_state.y_columns[i][0]) +
                    str(st.session_state.y_columns[i][1]))

# Creates Dynamic queries based on selection and
# runs the query to generate the count to populate the line graphs


def populate_graph(venue='', country='', cont='', publication_type='', auth_pos='', data_representation=''):

    global cursor
    sql_start = '''SELECT Year, count(PublicationID) as count\nFROM AllTogether '''
    sql_filter = '''\nWHERE '''
    sql_woman_filter = ''' AND (Gender = "woman")'''
    sql_end = '''\nGROUP BY Year;'''

    # the column/fiter names for each selection
    y_name = ''

    if 'data_representation' not in st.session_state:
        st.session_state.data_representation = data_representation

    if 'previous_data_representation' not in st.session_state:
        st.session_state.previous_data_representation = data_representation

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
            f2 = f2 + 'Country = "' + str(c) + '"'
            y_name = y_name+str(c)+'/'
        f2 = f2 + ')'
    if(cont == []):
        f3 = ''
    else:  # for the 'Continent' of Author
        f3 = '('
        for C in cont:
            if(C != cont[0]):
                f3 = f3 + ' or '
            f3 = f3 + 'Continent = "' + str(C) + '"'
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
        elif(auth_pos == 'Last author'):
            f4 = f4 + 'CAST(Position AS INT) = AuthorCount'
            y_name = y_name + 'Last author/'
        elif(auth_pos == 'Middle author'):
            f4 = f4 + 'Position > 1 AND CAST(Position AS INT) < AuthorCount'
            y_name = y_name + 'Middle author/'
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
    if(data_representation == 'Relative numbers'):
        show_percentage = True
        y_name = y_name + 'Percentage/'
    else:
        show_percentage = False
        y_name = y_name + 'Absolute/'
    # Dynamically arranging the queries based on input
    sql_logic = [f1, f2, f3, f4, f5]
    newf = ''
    f_count = 0
    for f in sql_logic:
        if(f != ''):
            if(f_count > 0):
                newf = newf + ' AND '
            f_count += 1
            newf = newf + f

    # Getting data to graph format
    year = pd.array(list(range(int(st.session_state.year_range[0]), int(
        st.session_state.year_range[1]))))

    # Checks if the query was already requested
    if(not [item for item in st.session_state.y_columns if y_name in item]):
        sql = sql_start + sql_filter + newf + sql_woman_filter + sql_end
        sql_non_woman = sql_start + sql_filter + newf + sql_end
        out = query_action(sql, 'store')
        if(show_percentage):
            sql = sql_start + sql_filter + newf + sql_end
            out_all = query_action(sql, 'store')

        y = []

        # TODO: Check if it really outputs the right percentage
        if(show_percentage):

            log(f'Out: {out}')
            log(f'Out_all: {out_all}')

            for i in year:
                print(i)

                if(i in out_all):
                    if(i in out):
                        out_all[i] = out[i]*100/out_all[i]
                    else:
                        out_all[i] = 0
                else:
                    out_all[i] = 0

                try:
                    y.append(out_all[i])
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
        st.session_state.y_columns.append([y_name, True, sql, sql_non_woman])

        if len(st.session_state.y_columns) > 1:
            line_graph_data = get_selected_df()
            line_graph_data['Year'] = [str(i) for i in year]
            line_graph_data = line_graph_data.set_index('Year')
            st.session_state.df_compare = line_graph_data
        else:
            line_graph_data = pd.DataFrame(
                {'Year': [str(i) for i in year], y_name: y}).set_index('Year')
    else:
        line_graph_data = get_selected_df()
        line_graph_data['Year'] = [str(i) for i in year]
        line_graph_data = line_graph_data.set_index('Year')
    st.line_chart(line_graph_data)


# get only the dataframes that the user selected below the chart
def get_selected_df():

    true_df = pd.DataFrame()

    for i in range(len(st.session_state.y_columns)):
        if st.session_state.y_columns[i][1] == True:
            true_df.insert(
                loc=0, column=st.session_state.y_columns[i][0], value=st.session_state.df_compare[st.session_state.y_columns[i][0]])

    return true_df

# the action of clearing all graphs and texts for the reset button


def clear_graphs():
    st.session_state.df_compare = pd.DataFrame()
    st.session_state.y_columns = []
    return


# Get general statistics about the data
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

    if 'publication_author_count' not in st.session_state:
        sql = '''SELECT count(DBLPName) as count\nFROM PublicationAuthor;'''
        cursor.execute(sql)
        st.session_state.publication_author_count = cursor.fetchall()[0][0]

    with st.expander('General statistics about the data'):
        col1, col2, col3 = st.columns(3)

        col1.markdown(
            f'**Publications count:** {st.session_state.publication_count}')
        col2.markdown(f'**Author count:** {st.session_state.author_count}')
        col3.markdown(
            f'**Affiliation count:** {st.session_state.affiliation_count}')

        col1.markdown(f'**Venue count:** {st.session_state.venue_count}')
        col2.markdown(
            f'**Publication Author count**: {st.session_state.publication_author_count}')
        col3.markdown(f'**Data source:** [dblp](https://dblp.org/)')

        col1.markdown(
            f'**Gender determination:** [GenderAPI](https://gender-api.com/)')

# Display all the filters that the user can select


def display_filters():
    global cursor

    if 'filters' not in st.session_state:
        st.session_state.filters = []

    if st.session_state.filters == [] or len(st.session_state.filters) < 4:
        # RETRIEVE OPTIONS for DISTINCT Conferences
        sql = '''SELECT DISTINCT Continent FROM AllTogether;'''
        cursor.execute(sql)
        result = cursor.fetchall()
        options_Continent = []
        for row in result:
            options_Continent.append(row[0])
        options_Continent = tuple(options_Continent)
        st.session_state.filters.append(options_Continent)

        sql = '''SELECT DISTINCT Country FROM AllTogether;'''
        cursor.execute(sql)
        result = cursor.fetchall()
        options_Country = []
        for row in result:
            options_Country.append(row[0])
        options_Country = tuple(options_Country)
        st.session_state.filters.append(options_Country)

        sql = '''SELECT DISTINCT Venue FROM AllTogether;'''
        cursor.execute(sql)
        result = cursor.fetchall()
        options_Venue = []
        for row in result:
            options_Venue.append(row[0])
        options_Venue = tuple(options_Venue)
        st.session_state.filters.append(options_Venue)

        sql = '''SELECT DISTINCT PublicationType FROM AllTogether;'''
        cursor.execute(sql)
        result = cursor.fetchall()
        options_Type = []
        for row in result:
            options_Type.append(row[0])
        options_Type = tuple(options_Type)
        st.session_state.filters.append(options_Type)

        # RETRIEVE OPTIONS for DISTINCT COUNTRY/CONTINENT
        # TODO: Get new options -> not working anymore

    # WIDGETs for the drop-down lists for selection
    col1, col2 = st.columns([1, 1])
    with col1:
        widget_cont = st.multiselect(
            'Filter by Continent:', st.session_state.filters[0], key='Cont')
        widget_venue = st.multiselect(
            'Filter by Conference/Journals:', st.session_state.filters[2], key='venue')
        data_representation = st.radio(
            'Data representation (Relative not properly working yet):', ('Absolute numbers', 'Relative numbers'))
    with col2:
        widget_count = st.multiselect(
            'Filter by Country:', st.session_state.filters[1], key='country')
        widget_pub_type = st.multiselect(
            'Filter by publication type:', st.session_state.filters[3], key='publication_type')
        widget_auth_pos = st.radio(
            'Filter by Woman Author Position:', ('First author', 'Any author', 'Middle author', 'Last author'), key='author_pos')

    logtxtbox = st.empty()

    # year-raneg selector for the drop-down lists for selection
    st.subheader("Year-range-selector")
    st.session_state.year_range[0], st.session_state.year_range[1] = st.slider(
        "Select years range:",  min_value=st.session_state.min_max[0], value=st.session_state.year_range, max_value=st.session_state.min_max[1])

    # button for clear history
    st.button('Clear History', on_click=clear_graphs)
    return(widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, logtxtbox, data_representation)


if __name__ == "__main__":
    main()
    # Closing the connection
    conn.close()
