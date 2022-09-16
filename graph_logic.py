import streamlit as st
import pandas as pd
from sqlite3 import Connection, connect
from PIL import Image
import prototype as pt
import plotly.figure_factory as ff
from utils import log

# Display all the filters that the user can select
def display_filters(cursor):

    if 'filters' not in st.session_state:
        st.session_state.filters = []

    if st.session_state.filters == [] or len(st.session_state.filters) < 4:
        sql = '''SELECT DISTINCT Continent FROM AllTogether ORDER BY Continent ASC;'''
        cursor.execute(sql)
        result = cursor.fetchall()
        options_Continent = []
        #print(result)
        for row in result:
            options_Continent.append(row[0])
        options_Continent = tuple(options_Continent)
        st.session_state.filters.append(options_Continent)
        # sql = '''SELECT DISTINCT Country, Continent FROM AllTogether ORDER BY Continent ASC;'''
        # cursor.execute(sql)
        # result = cursor.fetchall()
        # options_Continent = []
        # #print(result)
        # # for row in result:
        # #     options_Continent.append(row[0])
        # options_Continent = pd.DataFrame(result, columns=['Country', 'Continent'])
        # st.session_state.filters.append(options_Continent)
        # print(st.session_state.filters)

        sql = '''SELECT DISTINCT Country FROM AllTogether ORDER BY Country ASC;'''
        cursor.execute(sql)
        result = cursor.fetchall()
        options_Country = []
        for row in result:
            options_Country.append(row[0])
        options_Country = tuple(options_Country)
        st.session_state.filters.append(options_Country)

        sql = '''SELECT DISTINCT Venue FROM AllTogether ORDER BY Venue ASC;'''
        cursor.execute(sql)
        result = cursor.fetchall()
        options_Venue = []
        for row in result:
            options_Venue.append(row[0])
        options_Venue = tuple(options_Venue)
        st.session_state.filters.append(options_Venue)

        sql = '''SELECT DISTINCT PublicationType FROM AllTogether WHERE PublicationType <> "Proceedings" ORDER BY PublicationType ASC;'''
        cursor.execute(sql)
        result = cursor.fetchall()
        options_Type = []
        for row in result:
            options_Type.append(row[0])
        options_Type = tuple(options_Type)
        st.session_state.filters.append(options_Type)


    placeholder = st.empty()

    with st.form("Filters"):



        col1, col2 = st.columns([1, 1])
        with col1:
            widget_cont = st.multiselect(
                'Filter by Continent:', st.session_state.filters[0], key='cont', on_change=update_available_countries(cursor))
            
            widget_venue = st.multiselect(
                'Filter by Conference/Journals:', st.session_state.filters[2], key='venue')
        with col2:
            widget_count = st.multiselect(
                    'Filter by Country:', st.session_state.filters[1], key='country')
            widget_pub_type = st.multiselect(
                'Filter by publication type:', st.session_state.filters[3], key='publication_type')

        

        # year-range selector for the drop-down lists for selection
        st.subheader("Global Options")
        col1, col2 = st.columns([3, 1])
        with col1:
            year_range = st.slider(
            "Select years range:",  min_value=st.session_state.min_max[0], value=st.session_state.year_range, max_value=st.session_state.min_max[1], key='year_range')
            # if (st.session_state.year_range[0] != year_range[0]) or (st.session_state.year_range[1] != year_range1[1]):
            # on_change=update_graph
            #     st.session_state.year_range = year_range
        with col2:
            widget_auth_pos = st.radio(
                'Filter by Woman Author Position:', ('First author woman', 'Middle author woman', 'Last author woman', 'Any author woman'), key='author_pos')
            widget_data_representation = st.radio(
                'Select if the data will be shown in percentage or absolute numbers:', ['Absolute numbers', 'Relative numbers'], ) # on_change=update_graph

        clear_history_button = st.form_submit_button('Clear History', on_click=clear_history)

        button = st.form_submit_button('Submit and Compare')

        if button:
            update_graph(widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, widget_data_representation)

        # if clear_history_button:
        #     clear_history()

   # return(widget_venue, widget_count, widget_pub_type, widget_auth_pos)

def clear_history():
    st.session_state["auth_pos"] = "First author woman"
    
    st.session_state["cont"] = []
    st.session_state["venue"] = []
    st.session_state["country"] = []
    st.session_state["publication_type"] = []
    st.session_state["year_range"] = [2000, 2022]

    clear_graphs()
    

def update_available_countries(cursor):
    if not st.session_state.cont:
        sql = '''SELECT DISTINCT Country FROM AllTogether ORDER BY Country ASC;'''
    else:
        continent_filter = 'WHERE '

        for i in range(len(st.session_state.cont)):
            if i != 0:
                continent_filter = continent_filter + " OR "
            continent_filter = continent_filter + f"Continent=\"{st.session_state.cont[i]}\""

        sql = f'''SELECT DISTINCT Country, Continent FROM AllTogether {continent_filter} ORDER BY Country ASC;'''
         
    cursor.execute(sql)
    result = cursor.fetchall()
    options_Country = []
    for row in result:
        options_Country.append(row[0])
    options_Country = tuple(options_Country)
    st.session_state.filters[1] = options_Country

    

def update_graph(widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, widget_data_representation):
    st.session_state.widget_venue, st.session_state.widget_count, st.session_state.widget_count, st.session_state.widget_pub_type, st.session_state.widget_auth_pos, st.session_state.widget_data_representation = widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, widget_data_representation
    populate_graph(st.session_state.connection, widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos)


# Creates Dynamic queries based on selection and
# runs the query to generate the count to populate the line graphs
def populate_graph(conn: Connection, venue, country, cont, publication_type, auth_pos):
    sql_start = '''SELECT Year, count(PublicationID) as count\nFROM AllTogether '''
    sql_filter = '''\nWHERE '''
    sql_woman_filter = ''' AND (Gender = "woman")'''
    sql_end = '''\nGROUP BY Year;'''

    # if venue == '':
    #     venue = st.session_state.widget_venue
    # if country == '':
    #     country = st.session_state.widget_count
    # if cont == '':
    #     cont = st.session_state.widget_cont
    # if publication_type == '':
    #     publication_type = st.session_state.widget_pub_type
    # if auth_pos == '':
    #     auth_pos = st.session_state.widget_auth_pos

    # the column/fiter names for each selection
    y_name = ''

    change_year_range_df()
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
        with st.spinner('Creating graph...'):
            sql = sql_start + sql_filter + newf + sql_woman_filter + sql_end
            sql_non_woman = sql_start + sql_filter + newf + sql_end
            out = pt.query_action(sql, 'store')
            sql = sql_start + sql_filter + newf + sql_end
            out_all = pt.query_action(sql, 'store')


            y = []

            for Y in year:
                try:
                    y.append(out[Y])
                except:
                    y.append(0)
            st.session_state.df_compare[0][y_name] = y


            y = []
            print(year)
            for i in year:
                print('I: ' + str(i))
                print(out)
                if(i in out_all and i in out):
                    out_all[i] = out[i]*100/out_all[i]
                else:
                    out_all[i] = 0

                try:
                    y.append(out_all[i])
                except:
                    y.append(0)
    
            st.session_state.df_compare[1][y_name] = y

            y = pd.array(y)

            # construction of line_chart's data
            print(st.session_state.y_columns)
            st.session_state.y_columns.append([y_name, True, out, out_all])
            print(st.session_state.y_columns)
        
            y = pd.array(y)
    

    pd.options.plotting.backend = "plotly"

    line_graph_data = get_selected_df()
    line_graph_data['Year'] = [int(i) for i in year]

    line_graph_data = line_graph_data.set_index('Year')

    # if 'line_graph' not in st.session_state:
    #     st.session_state.line_graph = None

    fig = line_graph_data.plot()
    fig.update_layout(legend_title = 'Filters')

    if st.session_state.widget_data_representation == 'Relative numbers':
        fig.update_layout(yaxis_title='Percentage', yaxis_ticksuffix='%')
        # fig.layout.yaxis.ticksuffix = '%'
        # fig.layout.yaxis.title = 'Percentage'
    else:
        fig.update_layout(yaxis_title='Number of Publications')

    st.session_state.graph = fig
    #st.plotly_chart(fig, use_container_width=True) 

def change_year_range_df():
    st.session_state.line_chart = st.empty()

    if st.session_state.year_range != st.session_state.pyr:
        clear_graphs()
        st.session_state.pyr[0] = st.session_state.year_range[0]
        st.session_state.pyr[1] = st.session_state.year_range[1]
        

# get only the dataframes that the user selected below the chart
def get_selected_df():

    true_df = pd.DataFrame()
    #print(st.session_state.y_columns)
    for i in range(len(st.session_state.y_columns)):
        if st.session_state.y_columns[i][1] == True:
            if st.session_state.widget_data_representation == 'Absolute numbers':
                true_df.insert(
                    loc=0, column=st.session_state.y_columns[i][0], value=st.session_state.df_compare[0][st.session_state.y_columns[i][0]])
            else:
                true_df.insert(
                    loc=0, column=st.session_state.y_columns[i][0], value=st.session_state.df_compare[1][st.session_state.y_columns[i][0]])

    return true_df
    

def clear_graphs():
    print('Graphs cleared')
    st.session_state.df_compare = [pd.DataFrame(), pd.DataFrame()]
    st.session_state.y_columns = []
    st.session_state.graph = None

# Generate the checkboxes for the graphs to be displayed
def display_graph_checkboxes():
    st.subheader('Graph history')

    if len(st.session_state.y_columns) != 0:

        st.session_state.y_columns.sort(key=lambda x: x[1], reverse=True)

        for i in range(len(st.session_state.y_columns)):
            globals()['graph_checkbox_%s' % i] = st.checkbox(
                st.session_state.y_columns[i][0], value=st.session_state.y_columns[i][1], key=i)
            if globals()['graph_checkbox_%s' % i]:
                st.session_state.y_columns[i][1] = True
            else:
                st.session_state.y_columns[i][1] = False