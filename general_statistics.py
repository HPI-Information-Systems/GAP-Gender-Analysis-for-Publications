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
        f'**Publication Author count**: {st.session_state.publication_author_count}')
    col3.markdown(f'**Last time updated database:**  \n{datetime.strptime(st.session_state.last_time_updated, "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")}')

    col1.markdown(
        f'**Woman author count**:  \n{st.session_state.female_author_count}')
    col2.markdown(f'**Man author count**:  \n{st.session_state.male_author_count}')
    col3.markdown(f'**Authors with unkown gender**:  \n{st.session_state.unkown_author_count}')
    
    col1.markdown(f'**Authors with Country assigned (Wrong data):**  \n{st.session_state.authors_with_country}')
    col2.markdown(f'**Authors without Country assigned (Wrong data):** \n{st.session_state.authors_without_country}')
    col3.markdown(f'**Created by:**  \n[HPI Information Systems](https://hpi.de/naumann/home.html)')

    col1.markdown(f'**Data source:**  \n[dblp](https://dblp.org/)')
    col2.markdown(
        f'**Gender determination:**  \n[GenderAPI](https://gender-api.com/)')
    col3.markdown(f'**Illustrations by:**  \n[Undraw](https://undraw.co/)')

    # OR
    # with st.expander('General statistics about the data'):
    #     col1, col2, col3 = st.columns(3)

    #     col1.markdown(
    #         f'**Publications count:**  \n{st.session_state.publication_count}')
    #     col2.markdown(f'**Author count:**  \n{st.session_state.author_count}')
    #     col3.markdown(
    #         f'**Affiliation count:**  \n{st.session_state.affiliation_count}')

    #     col1.markdown(f'**Venue count:**  \n{st.session_state.venue_count}')
    #     col2.markdown(
    #         f'**Publication Author count**: {st.session_state.publication_author_count}')
    #     # Foormate date from st.session_state.last_time_updated to %d %b %Y
    #     col3.markdown(
    #         f'**Last time updated database:**  \n{datetime.strptime(st.session_state.last_time_updated, "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")}')

    #     col1.markdown(f'**Data source:**  \n[dblp](https://dblp.org/)')
    #     col2.markdown(
    #         f'**Gender determination:**  \n[GenderAPI](https://gender-api.com/)')
    #     col3.markdown(f'**Illustrations by:**  \n[Undraw](https://undraw.co/)')