import streamlit as st
import pandas as pd
from sqlite3 import Connection, connect
from datetime import datetime

# Get general statistics about the data
def display_general_statistics(cursor):

    if 'publication_count' not in st.session_state:
        sql = '''SELECT Value\nFROM GeneralStatistics WHERE Name = "PublicationCount";'''
        cursor.execute(sql)
        st.session_state.publication_count = cursor.fetchall()[0][0]

    if 'author_count' not in st.session_state:
        sql = '''SELECT Value\nFROM GeneralStatistics WHERE Name = "AuthorCount";'''
        cursor.execute(sql)
        st.session_state.author_count = cursor.fetchall()[0][0]
    if 'affiliation_count' not in st.session_state:
        sql = '''SELECT Value\nFROM GeneralStatistics WHERE Name = "AffiliationCount";'''
        cursor.execute(sql)
        st.session_state.affiliation_count = cursor.fetchall()[0][0]

    if 'venue_count' not in st.session_state:
        sql = '''SELECT Value\nFROM GeneralStatistics WHERE Name = "VenueCount";'''
        cursor.execute(sql)
        st.session_state.venue_count = cursor.fetchall()[0][0]

    if 'publication_author_count' not in st.session_state:
        sql = '''SELECT Value\nFROM GeneralStatistics WHERE Name = "PublicationAuthorCount";'''
        cursor.execute(sql)
        st.session_state.publication_author_count = cursor.fetchall()[0][0]

    if 'female_author_count' not in st.session_state:
        sql = '''SELECT Value\nFROM GeneralStatistics WHERE Name = "FemaleAuthorCount";'''
        cursor.execute(sql)
        st.session_state.female_author_count = cursor.fetchall()[0][0]
    if 'male_author_count' not in st.session_state:
        sql = '''SELECT Value\nFROM GeneralStatistics WHERE Name = "MaleAuthorCount";'''
        cursor.execute(sql)
        st.session_state.male_author_count = cursor.fetchall()[0][0]

    if 'unkown_author_count' not in st.session_state:
        sql = '''SELECT Value\nFROM GeneralStatistics WHERE Name = "UnkownAuthorCount";'''
        cursor.execute(sql)
        st.session_state.unkown_author_count = cursor.fetchall()[0][0]

    if 'last_time_updated' not in st.session_state:
        sql = '''SELECT Value\nFROM GeneralStatistics WHERE Name = "Date";'''
        cursor.execute(sql)
        st.session_state.last_time_updated = cursor.fetchall()[0][0]

    if 'authors_with_country' not in st.session_state:
        sql = '''SELECT Value \nFROM GeneralStatistics WHERE Name = "AuthorCountWithCountry";'''
        cursor.execute(sql)
        st.session_state.authors_with_country = cursor.fetchall()[0][0]
    
    if 'authors_without_country' not in st.session_state:
        sql = '''SELECT Value \nFROM GeneralStatistics WHERE Name = "AuthorCountWithoutCountry";'''
        cursor.execute(sql)
        st.session_state.authors_without_country = cursor.fetchall()[0][0]

    st.subheader('General statistics & Important information')
    
    col1, col2, col3 = st.columns(3)

    col1.markdown(
        f'**Publications count:**  \n{st.session_state.publication_count}')
    col2.markdown(f'**Author count:**  \n{st.session_state.author_count}')
    col3.markdown(
        f'**Affiliation count:**  \n{st.session_state.affiliation_count}')

    col1.markdown(f'**Venue count:**  \n{st.session_state.venue_count}')
    col2.markdown(
        f'**Publication Author count**:  \n{st.session_state.publication_author_count}')
    col3.markdown(f'**Last time updated database:**  \n{datetime.strptime(st.session_state.last_time_updated, "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")}')

    col1.markdown(
        f'**Woman author count**:  \n{st.session_state.female_author_count}')
    col2.markdown(f'**Man author count**:  \n{st.session_state.male_author_count}')
    col3.markdown(f'**Authors with unkown gender**:  \n{st.session_state.unkown_author_count}')
    
    col1.markdown(f'**Authors with Affiliation that has a Country assigned:**  \n{st.session_state.authors_with_country}')
    col2.markdown(f'**Authors with Affiliation that has not a Country assigned:**  \n{st.session_state.authors_without_country}')
    col3.markdown(f'**Created by:**  \n[HPI Information Systems](https://hpi.de/naumann/home.html)')

    col1.markdown(f'**Data source:**  \n[dblp](https://dblp.org/)')
    col2.markdown(
        f'**Gender determination:**  \n[GenderAPI](https://gender-api.com/)')
    col3.markdown(f'**Illustrations by:**  \n[Undraw](https://undraw.co/)')

    st.markdown('<h5>Important information</h5>', unsafe_allow_html=True)
    st.markdown('''Lorem ipsum dolor sit amet consectetur adipisicing elit. Maxime mollitia,
molestiae quas vel sint commodi repudiandae consequuntur voluptatum laborum
numquam blanditiis harum quisquam eius sed odit fugiat iusto fuga praesentium
optio, eaque rerum! Provident similique accusantium nemo autem. Veritatis
obcaecati tenetur iure eius earum ut molestias architecto voluptate aliquam
nihil, eveniet aliquid culpa officia aut! Impedit sit sunt quaerat, odit,
tenetur error, harum nesciunt ipsum debitis quas aliquid. Reprehenderit,
quia. Quo neque error repudiandae fuga? Ipsa laudantium molestias eos 
sapiente officiis modi at sunt excepturi expedita sint? Sed quibusdam
recusandae alias error harum maxime adipisci amet laborum. Perspiciatis 
minima nesciunt dolorem! Officiis iure rerum voluptates a cumque velit 
quibusdam sed amet tempora. Sit laborum ab, eius fugit doloribus tenetur 
fugiat, temporibus enim commodi iusto libero magni deleniti quod quam 
consequuntur! Commodi minima excepturi repudiandae velit hic maxime
doloremque. Quaerat provident commodi consectetur veniam similique ad 
earum omnis ipsum saepe, voluptas, hic voluptates pariatur est explicabo 
fugiat, dolorum eligendi quam cupiditate excepturi mollitia maiores labore 
suscipit quas? Nulla, placeat. Voluptatem quaerat non architecto ab laudantium
modi minima sunt esse temporibus sint culpa, recusandae aliquam numquam 
totam ratione voluptas quod exercitationem fuga. Possimus quis earum veniam 
quasi aliquam eligendi, placeat qui corporis!''')