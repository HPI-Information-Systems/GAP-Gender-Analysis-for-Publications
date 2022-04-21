from lxml import etree
import pandas as pd
from sqlite3 import Connection, connect
from utils import log
import os

if not os.path.exists('csv/db'):
    os.makedirs('csv/db')


DB = 'gap.db'
COUNTRIES = pd.read_csv('country_name_variations.csv')


def drop(conn, table):
    conn.execute(f"DROP TABLE IF EXISTS {table};")


def get_country_code(country):
    """
    Search for the given country in country_name_variations.csv and return the result(s).
    :param country:     string
    :return:    string, one of ISO 3166-1 alpha-2 country codes or empty string if no match was found in
                country_name_variations.csv
    """
    codes = COUNTRIES.loc[COUNTRIES.Country == country, 'Code'].values
    if len(codes) > 1:
        log(f"WARNING: more than one country code is found for extracted country {country}: {codes}")
    return codes


def fill_countries(conn: Connection, to_csv=False):
    """
    Get list of countries with unique names and country codes from countries_unique.csv, add continents and save
    everything to table 'Country' by using the given connection conn. If the table already exists it is dropped.
    :param conn:    sqlite3.Connection
    :param to_csv:  bool, whether to save the resulting table to csv/db/Country.csv, too.
    :return:
    """
    # Prevent pandas from interpreting Namibia's country code 'NA' as NaN value
    na_values = ["''", '#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan', '1.#IND', '1.#QNAN', '<NA>',
                 'N/A', 'NULL', 'NaN', 'n/a', 'nan', 'null']
    countries = pd.read_csv('countries_unique.csv', keep_default_na=False, na_values=na_values)
    continents = pd.read_csv('continents.csv', keep_default_na=False, na_values=na_values)
    Country = countries.merge(continents, on='Code')
    log('Continents to country list added')

    # Save countries to database
    Country.rename({'Country': 'DisplayName', 'Code': 'CountryCode'}, axis='columns', inplace=True)

    if to_csv:
        Country.to_csv('csv/db/Country.csv', index=False)

    drop(conn, 'Country')
    conn.execute("""
        CREATE TABLE Country(
            CountryCode TEXT PRIMARY KEY NOT NULL,
            DisplayName TEXT NOT NULL,
            Continent TEXT NOT NULL
        );
    """)

    Country.to_sql('Country', con=conn, if_exists='append', index=False)
    log('Countries written to database')


def fill_affiliations(conn: Connection, to_csv=False):
    """
    Parse unique affiliations from dblp.xml, extract their country (usually given at the end of an affiliation string),
    identify their country code and save everything to table 'Affiliation' by using the given connection conn. If the
    table already exists it is dropped.
    :param conn:    sqlite3.Connection
    :param to_csv:  bool, whether to save the resulting table to csv/db/Affiliation.csv, too.
    """
    context = etree.iterparse(source='dblp/dblp.xml', dtd_validation=True, load_dtd=True)

    # Extract affiliations from dblp xml
    raw_affiliations = set()
    for action, elem in context:
        if elem.tag == 'note' and elem.get('type') == 'affiliation' and elem.text is not None:
            # Remove leading and trailing spaces
            raw_affiliations.add(elem.text.strip())
        elem.clear()
    log("Affiliations from dblp extracted")

    # Extract country from affiliations and find country code
    affiliations = []
    for affiliation in raw_affiliations:
        splitted = affiliation.split(',')
        if len(splitted) > 1:
            potential_country = splitted[-1].strip()
            codes = get_country_code(potential_country)
            if len(codes) == 1:
                affiliations.append([affiliation, codes[0]])
            else:
                affiliations.append([affiliation, ''])
        else:
            affiliations.append([affiliation, ''])
    log("Countries to affiliations added")

    # Save affiliations to database
    Affiliation = pd.DataFrame(affiliations, columns=['FullAffiliation', 'CountryCode'])
    Affiliation.sort_values('FullAffiliation', inplace=True, ignore_index=True)

    if to_csv:
        Affiliation.to_csv('csv/db/Affiliation.csv', index=False)

    drop(conn, 'Affiliation')
    conn.execute("""
        CREATE TABLE Affiliation(
            AffiliationID INT NOT NULL PRIMARY KEY,
            FullAffiliation TEXT NOT NULL UNIQUE,
            Type TEXT,
            CountryCode TEXT,
            FOREIGN KEY(CountryCode) REFERENCES Country(CountryCode)
        );
    """)
    Affiliation.to_sql('Affiliation', con=conn, if_exists='append', index_label='AffiliationID')
    log("Affiliations written to database")


def main():
    conn = connect(DB)
    fill_countries(conn, to_csv=True)
    fill_affiliations(conn, to_csv=True)


if __name__ == "__main__":
    main()
