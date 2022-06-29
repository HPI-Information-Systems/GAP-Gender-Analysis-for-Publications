from lxml import etree
import pandas as pd
from sqlite3 import Connection, connect
from utils import log
import os
import ast
import re
import glob

if not os.path.exists('csv/db'):
    os.makedirs('csv/db')

if not os.path.exists('csv/GenderAPI/unprocessed'):
    os.makedirs('csv/GenderAPI/unprocessed')

DB = 'gap.db'
# For preventing pandas from interpreting Namibia's country code 'NA' as NaN value
NA_VALUES = ["''", '#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan', '1.#IND', '1.#QNAN', '<NA>',
             'N/A', 'NULL', 'NaN', 'n/a', 'nan', 'null']
COUNTRY_VARIATIONS = pd.read_csv('country_name_variations.csv', keep_default_na=False, na_values=NA_VALUES)
COUNTRIES = pd.read_csv('countries_unique.csv', keep_default_na=False, na_values=NA_VALUES)
CONTINENTS = pd.read_csv('continents.csv', keep_default_na=False, na_values=NA_VALUES)
# The, Zu, De, Den, Der, Del, Ul, Al, Da, El, Des, Di, Ten, Ter, Van, Von, Zur, Du, Das, Le actually are first names
NO_MIDDLE_NAMES = ['van', 'von', 'zur', 'aus', 'dem', 'den', 'der', 'del', 'de', 'la', 'La', 'las', 'le', 'los', 'ul',
                   'al', 'da', 'el', 'vom', 'Vom', 'auf', 'Auf', 'des', 'di', 'dos', 'du', 'ten', 'ter', "van't",
                   "Van't", 'of', 'het', 'the', 'af', 'til', 'zu', 'do', 'das', 'Sri', 'Si', 'della', 'Della', 'degli',
                   'Degli', 'Mc', 'Mac', 'und', 'on', "in't", 'i', 'ka', 't']


def main():
    conn = connect(DB)

    drop(conn, 'AuthorName')
    drop(conn, 'Author')
    drop(conn, 'GenderAPIResults')
    drop(conn, 'Affiliation')
    drop(conn, 'Country')

    # Do not enable the foreign key constraint checks before dropping the tables as this would make the dropping process
    # incredibly slow
    enable_foreign_key_constraints(conn)

    fill_countries(conn, to_csv=True)
    fill_affiliations(conn, to_csv=True)
    fill_gender_api_results(conn)
    fill_authors(conn, to_csv=True)  # Internally triggers fill_author_names()

    # Generate a csv file of first names with unknown gender that can be passed to the GenderAPI
    get_unknown_first_names(conn)


def drop(conn, table):
    conn.execute(f"DROP TABLE IF EXISTS {table};")


def enable_foreign_key_constraints(conn):
    conn.execute('PRAGMA foreign_keys = ON;')


def fill_countries(conn: Connection, to_csv=False):
    """
    Get list of countries with unique names and country codes from countries_unique.csv, add continents and save
    everything to table 'Country' by using the given connection conn.
    :param conn:    sqlite3.Connection
    :param to_csv:  bool, whether to save the resulting table to csv/db/Country.csv, too.
    :return:
    """
    log('Progress of filling countries started')
    Country = COUNTRIES.merge(CONTINENTS, on='Code')
    log('Continents to country list added')

    # Save countries to database
    Country.rename({'Country': 'DisplayName', 'Code': 'CountryCode'}, axis='columns', inplace=True)

    if to_csv:
        Country.to_csv('csv/db/Country.csv', index=False)

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
    identify their country code and save everything to table 'Affiliation' by using the given connection conn.
    :param conn:    sqlite3.Connection
    :param to_csv:  bool, whether to save the resulting table to csv/db/Affiliation.csv, too.
    """
    log('Progress of filling affiliations started')
    context = etree.iterparse(source='dblp/dblp.xml', dtd_validation=True, load_dtd=True)

    # Extract affiliations from dblp xml
    raw_affiliations = set()
    for action, elem in context:
        if elem.tag == 'note' and elem.get('type') == 'affiliation' and elem.text is not None:
            # Remove leading and trailing spaces
            raw_affiliations.add(elem.text.strip())
        elem.clear()
    log('Affiliations from dblp extracted')

    # Extract country from affiliations and find country code
    affiliations = []
    for affiliation in raw_affiliations:
        affiliations.append(_assign_country_code(affiliation))
    log('Countries to affiliations added')

    # Save affiliations to database
    Affiliation = pd.DataFrame(affiliations, columns=['FullAffiliation', 'CountryCode'])
    Affiliation.sort_values('FullAffiliation', inplace=True, ignore_index=True)

    if to_csv:
        Affiliation.to_csv('csv/db/Affiliation.csv', index=False)

    conn.execute("""
        CREATE TABLE Affiliation(
            AffiliationID INT NOT NULL PRIMARY KEY,
            FullAffiliation TEXT NOT NULL UNIQUE,
            Type TEXT,
            CountryCode TEXT,
            FOREIGN KEY(CountryCode) REFERENCES Country(CountryCode) ON DELETE CASCADE
        );
    """)
    Affiliation.to_sql('Affiliation', con=conn, if_exists='append', index_label='AffiliationID')
    log('Affiliations written to database')


def fill_gender_api_results(conn: Connection, gapi_path='csv/GenderAPI/', ):
    """
    Read csv file given under gapi_path or, if it's a directory, read each csv file located there, concatenate them,
    drop duplicates and save everything to table 'GenderAPIResults' by using the given connection conn.
    This function assumes all csv files in gapi_path to have semicolons as separators as that's the way they are
    returned by the GenderAPI.
    :param conn:        sqlite3.Connection
    :param gapi_path:   relative path to csv file(s) returned by the GenderAPI
    """
    log('Progress of filling GenderAPI results started')

    if '.csv' in gapi_path:
        GenderAPIResults = pd.read_csv(gapi_path, sep=';')
    else:
        glob_path = os.path.join(gapi_path, '*.csv')
        GenderAPIResults = pd.DataFrame()
        for csv_file in glob.glob(glob_path):
            GenderAPIResults = pd.concat([GenderAPIResults, pd.read_csv(csv_file, sep=';')])

    # Remove duplicates
    GenderAPIResults.drop_duplicates(inplace=True)

    # Rename columns to wanted sql columns
    GenderAPIResults.rename(columns={'first_name': 'FirstName', 'ga_first_name': 'GaFirstName', 'ga_gender': 'GaGender',
                                     'ga_accuracy': 'GaAccuracy', 'ga_samples': 'GaSamples'}, inplace=True)

    # Some names that are now known by GenderAPI were unknown in previous requests
    # These names occur several times in GenderAPIResults.FirstName and the entries with NaN values in every column but
    # FirstName needs to be deleted
    # Thus, we sort first such that entries with the highest power (GaSamples) are listed before their unknown
    # duplicates and then drop any but the first entry for each duplicated FirstName
    if not GenderAPIResults.empty:
        GenderAPIResults.sort_values(by=['FirstName', 'GaSamples'], ascending=[True, False], inplace=True)
        GenderAPIResults.drop_duplicates(subset=['FirstName'], keep='first', inplace=True)

    conn.execute("""
        CREATE TABLE GenderAPIResults(
            FirstName TEXT NOT NULL PRIMARY KEY,
            GaFirstName TEXT,
            GaGender TEXT,
            GaAccuracy INT,
            GaSamples INT
        );
    """)
    GenderAPIResults.to_sql('GenderAPIResults', con=conn, if_exists='append', index=False)
    log('GenderAPI results written to database')


def fill_authors(conn: Connection, to_csv=False):
    """
    Extract persons from dblp's www entries with title 'Home Page' (See https://dblp.org/faq/1474690.html.)
    Expect to find 'csv/www.csv', a csv file of www entries, generated by dblp_parser.py. Use first (full) name in
    column author as DBLPName and triggers propagation of table AuthorName with the remaining full names in list. Pick
    first affiliation only for a person in case multiple ones are listed and not specified further (See
    _prepare_affiliations() for details). Extracts Orcid and GoogleScholar pages from column url and puts the remaining
    ones to a separate column named Homepages. Determine the gender of each author (see _determine_genders() for
    details) and also save the first name that lead to this decision. Save everything to table 'Author' by using the
    given connection conn.
    :param conn:                sqlite3.Connection
    :param to_csv:              bool, whether to save the resulting table to csv/db/AuthorName.csv, too.
    """
    log('Progress of filling authors started')
    www = pd.read_csv('csv/www.csv')

    # Drop modification date, entries not referring to actual authors and title (turned useless)
    www.drop(['mdate'], axis='columns', inplace=True)
    www = www[www.title == 'Home Page']
    www.drop(['title'], axis='columns', inplace=True)
    www = www[www.author.notnull()]

    # Extract name dblp uses on a person's page and corresponding alternative names
    www['DBLPName'], alternative_names = _separate_names(www.author)

    # Extract a person's first affiliation that is not specified further (See _prepare_affiliations() for details)
    www['affiliation'] = _prepare_affiliations(www[['key', 'note']])
    www.drop(columns=['note'], inplace=True)

    # Get AffiliationID from table Affiliation by mapping 'affiliation' with Affiliation.FullAffiliation
    Affiliation = pd.read_sql('SELECT AffiliationID, FullAffiliation FROM Affiliation', con=conn)
    Author = www.merge(Affiliation, how='left', left_on='affiliation',
                       right_on='FullAffiliation').astype({'AffiliationID': 'Int64'})
    Author.drop(columns=['FullAffiliation', 'affiliation'], inplace=True)
    log('AffiliationIDs to authors added')

    # Get a person's web pages by extracting Orcid and GoogleScholar pages from the urls and fill column Homepages with
    # remaining urls separated by newlines
    Author['OrcidPage'], Author['GoogleScholarPage'], Author['Homepages'] = zip(*Author.url.apply(lambda x:
                                                                                                  _prepare_urls(x)))
    Author.drop(columns=['url'], inplace=True)
    log('Web pages of authors extracted and added')

    # Determine genders
    log("Gender determination process started")
    Author['Gender'], Author['FirstName'] = _determine_genders(Author.DBLPName, alternative_names, conn)
    # Groups should not have a gender
    Author.loc[Author.publtype == 'group', ['Gender', 'FirstName']] = 'unknown', None
    log('Genders of authors determined')

    # Rename columns to wanted sql columns
    Author.rename(columns={'key': 'AuthorID', 'publtype': 'Type'}, inplace=True)
    Author.drop(columns=['author'], inplace=True)

    # Save authors to database
    if to_csv:
        Author.to_csv('csv/db/Author.csv', index=False)

    conn.execute("""
                CREATE TABLE Author(
                    AuthorID TEXT NOT NULL PRIMARY KEY,
                    DBLPName TEXT NOT NULL UNIQUE,
                    Type TEXT,
                    OrcidPage TEXT,
                    GoogleScholarPage TEXT,
                    Homepages TEXT,
                    AffiliationID INT,
                    Gender TEXT,
                    FirstName TEXT,
                    FOREIGN KEY(AffiliationID) REFERENCES Affiliation(AffiliationID) ON DELETE CASCADE
                );
            """)
    Author.to_sql('Author', con=conn, if_exists='append', index=False)
    log('Authors written to database')

    # Trigger filling the table AuthorName
    fill_author_names(alternative_names, conn, to_csv=to_csv)


def fill_author_names(author_names, conn: Connection, to_csv=False):
    """
    Save the given author_names to table 'AuthorName' by using the given connection conn.
    :param author_names:    pd.DataFrame, being the return value 'alternative_names' of function _separate_names() with
                            columns 'DBLPName' and 'FullName'.
    :param conn:            sqlite3.Connection
    :param to_csv:          bool, whether to save the resulting table to csv/db/AuthorName.csv, too.
    """
    log('Progress of filling author names started')
    if to_csv:
        author_names.to_csv('csv/db/AuthorName.csv', index=False)

    conn.execute("""
            CREATE TABLE AuthorName(
                AuthorNameID INT NOT NULL PRIMARY KEY,
                DBLPName TEXT NOT NULL,
                FullName TEXT NOT NULL UNIQUE,
                FOREIGN KEY(DBLPName) REFERENCES Author(DBLPName) ON DELETE CASCADE
            );
        """)
    author_names.to_sql('AuthorName', con=conn, if_exists='append', index_label='AuthorNameID')
    log('Author names written to database')


def get_unknown_first_names(conn: Connection):
    unknown = pd.read_sql("""
        SELECT DISTINCT FirstName AS first_name FROM Author 
        WHERE Gender = 'unknown' AND FirstName NOT NULL ORDER BY FirstName;
        """, con=conn)

    # Discard 'nobiliary' particles in first names
    unknown = unknown[~unknown.first_name.isin(NO_MIDDLE_NAMES)]

    unknown.to_csv('csv/GenderAPI/unprocessed/first_names.csv', index=False)


def _assign_country_code(affiliation):
    """
    Extract the country from the given affiliation by using the following rules of thumb:
    1. Most affiliations separate information by comma with the country at the last position
    2. Some affiliations do not separate information by comma but still contain the country as the last word (in case it
    is a single word country). Every other way of containing the country in the affiliation is not supported.
    The country code is then identified by _read_country_code(). If more than one country code is found, no country code
    is assigned to the affiliation and _read_country_code() writes a warning to STDOUT.
    :param affiliation: String, containing the full affiliation listed in dblp
    :return: list of given affiliation and country code, if found. Otherwise, country code is an empty string.
    """
    country_code = None
    codes_found = []

    # Most affiliations list the country after last comma
    splitted_affilation = affiliation.split(',')

    if len(splitted_affilation) > 1:
        potential_country = splitted_affilation[-1].strip()
        codes_found = _read_country_code(potential_country)
        if len(codes_found) == 1:
            country_code = codes_found[0]

    # Some affiliations do not separate the information by comma but still contain the country as the last word
    splitted_affilation = affiliation.split(' ')
    if len(codes_found) == 0:
        potential_country = splitted_affilation[-1].strip()
        codes_found = _read_country_code(potential_country)
        if len(codes_found) == 1:
            country_code = codes_found[0]
    return [affiliation, country_code]


def _read_country_code(country):
    """
    Search for the given country in country_name_variations.csv and return the result(s).
    :param country:     string
    :return:    string, one of ISO 3166-1 alpha-2 country codes or empty string if no match was found in
                country_name_variations.csv
    """
    codes = COUNTRY_VARIATIONS.loc[COUNTRY_VARIATIONS.Country == country, 'Code'].values
    if len(codes) > 1:
        log(f"WARNING: more than one country code is found for extracted country {country}: {codes}")
    return codes


def _separate_names(authors):
    """
    Split an author's names into their DBLPName (first (full) name in a row of given series authors) and corresponding
    alternative names.
    :param authors:     pd.Series, containing all names of one person per row separated by newlines.
    :return:            tuple of    1. pd.Series, containing the DBLPNames with the same indices as given in authors and
                                    2. pd.DataFrame, with columns 'DBLPName' and 'FullName', each FullName is an
                                    alternative name of an author identifiable via their DBLPName.
    """
    author_names = pd.DataFrame(columns=['DBLPName', 'FullName'])
    author_names['DBLPName'], author_names['FullName'] = authors.str.split("\n").str[0], authors.str.split("\n").str[1:]

    # Extract actual name if additional author information are given via dict
    author_names.DBLPName = author_names.DBLPName.apply(
        lambda x: ast.literal_eval(x)['text'] if x.find('{') == 0 else x)

    # Drop authors with one name only from alternative_names
    dblp_names = author_names.DBLPName.drop_duplicates()
    alternative_names = author_names[author_names.FullName.str.len() > 0]

    # Create a row per alternative FullName of a person
    alternative_names = alternative_names.explode('FullName')

    # Extract actual name if additional author information are given via dict
    alternative_names.FullName = alternative_names.FullName.apply(
        lambda x: ast.literal_eval(x)['text'] if x.find('{') == 0 else x)
    alternative_names.reset_index(drop=True, inplace=True)

    return dblp_names, alternative_names


def _prepare_affiliations(www):
    """
    Expect column note of df www to contain dblp.xml's notes of www entries separated by newline in case of multiple
    notes per person. Pick the first affiliation only in case multiple ones are listed in and not specified further by
    a type like 'award', 'uname', 'isnot' or 'former' or by a label like 'former' or specific period of time
    :param www: pd.Dataframe
    :return: pd.Series, containing one affiliation (or none) for each person that was given in df www.
    """
    www = www.copy()
    www.note = www.note.apply(lambda x: x.split("\n") if pd.notnull(x) else '')
    www = www.explode('note')

    # Split notes into type, label and text for easier handling
    www['label'] = www.note.apply(
        lambda x: ast.literal_eval(x)['label'] if x.find('{') == 0 and 'label' in ast.literal_eval(x) else None)
    www['type'] = www.note.apply(
        lambda x: ast.literal_eval(x)['type'] if x.find('{') == 0 and 'type' in ast.literal_eval(x) else None)
    www['text'] = www.note.apply(
        lambda x: ast.literal_eval(x)['text'] if x.find('{') == 0 and 'text' in ast.literal_eval(x) else None)
    www.drop(columns=['note'], inplace=True)

    # Drop unnecessary note types like 'award', 'uname', 'isnot' and 'former'
    www = www[www.type.isin(['affiliation', None])]

    # Drop affiliations with labels (usually 'former' or a specific period of time)
    www = www[((www.type == 'affiliation') & (www.label.isnull())) | (www.type.isnull())]

    # Pick first affiliation only in case multiple ones are listed and not specified further
    persons_with_multiple_affiliations = www[www.duplicated(subset=['key'], keep='first')].shape[0]
    log(f"Number of persons with multiple affiliations not specified further: {persons_with_multiple_affiliations}")
    # www[www.duplicated(subset=['key'], keep=False)].to_csv('csv/persons_with_multiple_affiliations.csv', index=False)
    www.drop_duplicates(subset=['key'], keep='first', inplace=True)
    return www['text']


def _prepare_urls(urls):
    """
    Separates web pages of a person into ORCID pages, Google Scholar pages and remaining ones. If there are multiple
    pages of one kind, they are separated by a \n . Some urls from dblp come with a type like 'archive' which get
    appended to the respective url in brackets (See _append_type() for details).
    :param urls:    String, containing urls separated by \n (or dictionaries containing additional information about one
                    url) from dblp.
    :return:        triple of strings, first one contains all orcid pages, second one all google scholar pages and last
                    one all remaining web pages of a person.
    """
    orcid_page = []
    google_scholar_page = []
    homepages = []

    urls = urls.split("\n") if pd.notnull(urls) else None

    if urls:
        for url in urls:
            url = _append_type(url)
            if 'orcid.org' in url:
                orcid_page.append(url)
            elif 'scholar.google.com' in url:
                google_scholar_page.append(url)
            else:
                homepages.append(url)

    orcid_page = "\n".join(orcid_page) if len(orcid_page) > 0 else None
    google_scholar_page = "\n".join(google_scholar_page) if len(google_scholar_page) > 0 else None
    homepages = "\n".join(homepages) if len(homepages) > 0 else None

    return orcid_page, google_scholar_page, homepages


def _append_type(url):
    """
    Check if the given url is a dictionary containing additional information from dblp and extracts the url and the type
    (like 'deprecated' or 'archive').
    :param url: string, containing a dictionary with the url given in 'text'
    :return: string, the url given in url['text'] followed by url['type'] in brackets if given
    """
    if url and url.find('{') == 0:
        url = ast.literal_eval(url)
        return url['text'] + ' (' + url['type'] + ')' if 'type' in url else url['text']
    else:
        return url


def _determine_genders(dblp_names: pd.Series, alternative_names: pd.DataFrame, conn: Connection):
    """
    Assign a gender to all authors by first checking the first name in a DBLPName (middle name(s) of the DBLPName are
    only used if the first name is abbreviated, see _get_checkable_first_name()).
    Todo: Actually check middle name(s)' gender if first name is unknown or neutral.
    Todo: If no gender could be found for the DBLPName (or it was determined as 'unknown' by the GenderAPI meaning it is
    a neutral name), search for alternative names in table 'AuthorName' and checks the gender for them.
    :param dblp_names:          pd.Series,
    :param alternative_names:   pd.DataFrame, being the return value 'alternative_names' of function _separate_names()
                                with columns 'DBLPName' and 'FullName'.
    :param conn:                sqlite3.Connection
    :return:                    tuple of pd.Series', first one contains the gender for each given DBLPName and second
                                one the first name that was used to determine the gender. Both have the same indices as
                                given dblp_names. If there is no first name for a given DBLPName in the second series,
                                the name was not found in the table 'GenderAPIResults'.
    """
    authors = pd.DataFrame()
    authors['DBLPName'] = dblp_names

    # Read mappings from first names to genders by GenderAPI from database
    log('read_sql GenderAPIResults started')
    GenderAPIResults = pd.read_sql('SELECT FirstName, GaGender FROM GenderAPIResults', con=conn)
    log('read_sql GenderAPIResults ended')

    log('get_checkable_first_names started')
    authors['FirstName'] = authors.DBLPName.apply(lambda x: _get_checkable_first_name(x))
    log('get_checkable_first_names ended')

    # Give DBLPNames a gender based on column FirstName
    log('merge Author and GenderAPIResults started')
    authors = authors.merge(GenderAPIResults[['FirstName', 'GaGender']], how='left', on='FirstName')
    log('merge Author and GenderAPIResults ended')

    # WIP:
    # Check the gender of alternative names if necessary
    # log('check for alternative names started')
    # authors.FirstName, authors.GaGender = _check_alternative_names(authors, alternative_names, conn, GenderAPIResults)
    # a = pd.DataFrame()
    # a['FirstName'], a['GaGender'] = _check_alternative_names(authors, alternative_names, conn, GenderAPIResults)
    # log('check for alternative names ended')
    # log(f"Shape of authors: {authors.shape}")
    # log(f"Shape of authors with alternative names: {a.shape}")

    authors.rename(columns={'GaGender': 'Gender'}, inplace=True)
    authors.Gender = authors.Gender.apply(lambda x: _map_gender_terms(x))
    log('merge alternative names and GenderAPIResults ended')

    return authors.Gender, authors.FirstName


def _get_checkable_first_name(DBLPName):
    """
    Return the first name out of the first and middle names that is not abbreviated (or a nobiliary particle) and clean
    the names from quotes, brackets and trailing numbers being common in dblp's author names. If only one word is given
    in DBLPName the first name cannot be determined.
    :param DBLPName:    String, following the pattern 'first_name middle_name(s) last_name', middle name(s) are optional
    :return:            String, first usable first name out of first_name and middle_name(s)
    """
    # Remove trailing numbers that may appear in DBLPName and split it into list
    fullname = DBLPName.rstrip(' 0123456789').split(' ')
    # Can't determine if this is just the first or just the last name
    if len(fullname) == 1:
        return None

    # Split into first name, middle name(s) and last name
    first_name, middle_names, last_name = fullname[0], fullname[1:-1], fullname[-1]

    # Discard quotes and brackets
    first_name = first_name.strip("()\"")
    middle_names = [middle_name.strip("()'\"") for middle_name in middle_names]
    last_name = last_name.strip("()'\"")

    # Discard 'nobiliary' particles in middle_names
    middle_names = [middle_name for middle_name in middle_names if middle_name not in NO_MIDDLE_NAMES]

    # Discard abbreviations and check for middle names if necessary
    if re.match(r'\w+[.]', first_name):
        result = _get_checkable_first_name(' '.join(middle_names + [last_name]))
        return result

    return first_name


def _check_alternative_names(authors, alternative_names, GenderAPIResults):
    """
    WIP, see Todos.
    Check the gender for alternative names of an author if their DBLPName has the gender 'unknown' or 'neutral'.
    :param authors:             pd.DataFrame, being a join result of DBLPNames and GenderAPIResults with columns
                                'DBLPName', 'FirstName', 'GaGender'
    :param alternative_names:   pd.DataFrame, being the return value 'alternative_names' of function
                                _separate_names() with columns 'DBLPName' and 'FullName'.
    :param GenderAPIResults:    pd.DataFrame, with columns 'FirstName' and 'GaGender' from table 'GenderAPIResults'
    :return:                    tuple of pd.Series, 'FirstName' and 'GaGender'
    """
    print(authors.shape)
    print(alternative_names.shape)
    alternative_names = authors[['DBLPName', 'FirstName', 'GaGender']].merge(
        alternative_names[['DBLPName', 'FullName']], how='left', on='DBLPName')
    print(alternative_names.shape)
    print(alternative_names.columns)

    alternative_names.rename(columns={'FirstName': 'FirstName_DBLPName'}, inplace=True)
    alternative_names['FirstName_AlternativeName'] = alternative_names.apply(
        lambda x: _get_checkable_first_name(x.FullName)
        if pd.notnull(x.FullName) and (x.GaGender == 'unknown' or pd.isnull(x.GaGender)) else None, axis=1)

    alternative_names = alternative_names.merge(GenderAPIResults[['FirstName', 'GaGender']], how='left',
                                                left_on='FirstName_AlternativeName', right_on='FirstName')

    def reduce_gender(row):
        # WIP: It only picks the more meaningful gender and first name per pair of DBLPName and alternative name
        # In case of multiple alternative names per DBLPName there is still the need for more reduction
        if row.GaGender_x != 'unknown' and pd.notnull(row.GaGender_x):
            return [row.FirstName_DBLPName, row.GaGender_x]
        else:
            return [row.FirstName_AlternativeName, row.GaGender_y]

    alternative_names.drop(columns=['FirstName'], inplace=True)

    log('Reduce the gender started')
    alternative_names[['FirstName', 'GaGender']] = alternative_names.apply(reduce_gender, axis=1,
                                                                           result_type='expand')
    log('Reduce the gender ended')
    alternative_names.to_csv('csv/alternative_names_with_gender.csv', index=False)
    # Todo: _get_gender() could be used as well to determine the gender for the names one by one (less efficient!)
    # _get_gender() needs 11 minutes for all dblp_names
    # authors['GaGender'] = authors.FirstName_y.apply(lambda x: get_gender(x, conn))
    # Todo: shrink return series (pick one of the alternative first names, e.g. first one, and pick its gender'

    return alternative_names.FirstName, alternative_names.GaGender


def _get_gender(firstname, conn):
    """
    Map the gender from table 'GenderAPIResults' to the given firstname.
    A gender determined by the GenderAPI is one out of 'female', 'male', 'unknown' (in case of a unisex name) or none.
    :param firstname:   String
    :param conn:        sqlite3.Connection
    :return:            String or None, one of ['female', 'male', 'unknown', None]
    """
    if firstname is None:
        return None

    # Change single apostrophe to SQL's style of apostrophes
    firstname = firstname.replace("'", "''")
    result = pd.read_sql(f"SELECT GaGender FROM GenderAPIResults where FirstName = '{firstname}'", con=conn)

    return result['GaGender'].iloc[0] if not result.empty else None


def _map_gender_terms(gender):
    """
    Return the final wording for the given gender. 'female' and 'male' are mapped to 'woman' and 'man'. 'unknown' as
    given by the GenderAPI means the corresponding name is actually used by man and woman equally and therefore being
    'neutral'. If no gender was determined by the GenderAPI, it is labeled as 'unknown'.
    :param gender:  String
    :return:        String
    """
    mapping = {'female': 'woman',
               'male': 'man',
               'unknown': 'neutral'}
    if gender in mapping:
        return mapping[gender]
    else:
        return 'unknown'


if __name__ == "__main__":
    main()
