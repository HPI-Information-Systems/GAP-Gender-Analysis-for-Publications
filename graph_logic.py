import streamlit as st
import pandas as pd
from sqlite3 import Connection, connect
from PIL import Image
import prototype as pt

# Display all the filters that the user can select
def display_filters(cursor):

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

        sql = '''SELECT DISTINCT PublicationType FROM AllTogether WHERE PublicationType <> "Proceedings";'''
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
            'Filter by Woman Author Position:', ('First author woman', 'Middle author woman', 'Last author woman', 'Any author woman'), key='author_pos')

    logtxtbox = st.empty()

    # year-raneg selector for the drop-down lists for selection
    st.subheader("Year-range-selector")
    st.session_state.year_range[0], st.session_state.year_range[1] = st.slider(
        "Select years range:",  min_value=st.session_state.min_max[0], value=st.session_state.year_range, max_value=st.session_state.min_max[1])

    # button for clear history
    st.button('Clear History', on_click=clear_graphs)
    return(widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, logtxtbox, data_representation)

# Creates Dynamic queries based on selection and
# runs the query to generate the count to populate the line graphs
def populate_graph(conn: Connection, venue='', country='', cont='', publication_type='', auth_pos='', data_representation=''):
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
        if(auth_pos == 'First author woman'):
            f4 = f4 + 'Position = "1"'
            y_name = y_name + 'First author woman/'
            # If any author, everyone, including first author
        elif(auth_pos == 'Last author woman'):
            f4 = f4 + 'CAST(Position AS INT) = AuthorCount'
            y_name = y_name + 'Last author woman/'
        elif(auth_pos == 'Middle author woman'):
            f4 = f4 + 'Position > 1 AND CAST(Position AS INT) < AuthorCount'
            y_name = y_name + 'Middle author woman/'
        else:
            f4 = f4 + 'Position = "1" OR Position <> "1"'
            y_name = y_name + 'Any author woman/'
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
        out = pt.query_action(sql, 'store')
        if(show_percentage):
            sql = sql_start + sql_filter + newf + sql_end
            out_all = pt.query_action(sql, 'store')

        y = []

        # TODO: Check if it really outputs the right percentage
        if(show_percentage):
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

# Generate the checkboxes for the graphs to be displayed

def display_graph_checkboxes():
    st.subheader('Graph history')

    if len(st.session_state.y_columns) == 0:
        st.markdown(
            "<h5 style='text-align: center;'>You have not selected any graphs yet </h5>", unsafe_allow_html=True)

        image = Image.open('assets/no_data.png')

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write('')

        with col2:
            st.image(image, use_column_width=True)

        with col3:
            st.write('')
    else:
        st.session_state.y_columns.sort(key=lambda x: x[1], reverse=True)
        for i in range(len(st.session_state.y_columns)):
            globals()['graph_checkbox_%s' % i] = st.checkbox(
                st.session_state.y_columns[i][0], value=st.session_state.y_columns[i][1], key=i)
            if globals()['graph_checkbox_%s' % i]:
                st.session_state.y_columns[i][1] = True
            else:
                st.session_state.y_columns[i][1] = False
