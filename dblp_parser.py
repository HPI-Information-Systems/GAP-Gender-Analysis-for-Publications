import re
import os
from lxml import etree
import pandas as pd
from utils import log

if not os.path.exists("csv"):
    os.makedirs("csv")


def extract_title(title_element):
    """
    Remove html formatting elements etc. from title
    :param title_element: xml element
    :return:    string
    """
    title = re.sub("<.*?>", "", etree.tostring(title_element).decode("utf-8")).rstrip(
        "\n"
    )
    return title


def extract_feature(elem, features):
    """
    Extract the value of each feature of the element as well as its attributes.
    :param elem:        lxml.etree.Element, the element whose features are to be extracted.
    :param features:    List of strings, the to be extracted sub-elements of elem

    :return:    Dict of attributes and sub-elements of elem. Sub-elements are encoded as dicts if they have attributes,
                otherwise they contain only their text values.
    """
    attribs = {}
    # Extract attributes of level-1 element
    for attribute in elem.attrib:
        attribs[attribute] = elem.attrib[attribute]

    # Extract wanted sub-elements
    for sub in elem:
        if sub.tag not in features:
            continue
        elif sub.tag == "title":
            text = extract_title(sub)
        else:
            text = sub.text
        if text is not None and len(text) > 0:
            # If a sub-element has attributes, create a dictionary out of them and add its text
            if sub.attrib:
                text = str({**sub.attrib, **{"text": text}}) if sub.attrib else text
            # Concatenate text/dict of multiple sub-elements with the same tag with line breaks
            attribs[sub.tag] = (attribs.get(sub.tag, "") + "\n" + text).lstrip("\n")
    # Remove content of processed elem from the tree to save memory
    elem.clear()

    return attribs


def extract_entity(
    entity, features, dblp_path, save_path=None, ignorable_elements=None
):
    """
    Parse specific elements according to the given type name and features.
    :param entity:              string, has to be same as the xml element tag
    :param features:            list of strings, the tags of sub-elements of entity
    :param dblp_path:           string, path the dblp.xml and dblp.dtd
    :param save_path:           string, csv save path including file name and extension '.csv', default: None
                                If None, it does not save the results.
    :param ignorable_elements:  list of strings, the tags of level one xml elements unequal entity

    :return:    pandas.DataFrame with attributes and sub-elements of entity as columns
    """
    log(f"PROCESS: Start parsing for {entity}...")
    results = []
    for _, elem in etree.iterparse(
        source=dblp_path, dtd_validation=True, load_dtd=True
    ):
        if elem.tag == entity:
            attrib_values = extract_feature(elem, features)
            results.append(attrib_values)
        elif ignorable_elements and elem.tag in ignorable_elements:
            # Remove content of needless elems from the tree to save memory
            elem.clear()

    df = pd.json_normalize(results)
    if save_path:
        df.to_csv(save_path, index=False)
    return df


def main():
    dblp_path = "dblp/dblp.xml"

    key_features = {
        "article": [
            "author",
            "ee",
            "journal",
            "number",
            "pages",
            "title",
            "url",
            "volume",
            "year",
        ],
        "book": [
            "author",
            "ee",
            "isbn",
            "pages",
            "publisher",
            "series",
            "title",
            "volume",
            "year",
        ],
        "inproceedings": [
            "author",
            "booktitle",
            "crossref",
            "ee",
            "pages",
            "title",
            "url",
            "year",
        ],
        "proceedings": [
            "booktitle",
            "editor",
            "ee",
            "isbn",
            "publisher",
            "series",
            "title",
            "url",
            "volume",
            "year",
        ],
        "incollection": [
            "author",
            "booktitle",
            "crossref",
            "ee",
            "pages",
            "title",
            "url",
            "year",
        ],
        "phdthesis": ["author", "ee", "isbn", "pages", "school", "title", "year"],
        "mastersthesis": ["author", "ee", "note", "school", "title", "year"],
        "www": ["author", "note", "title", "url"],
    }

    for element in key_features.keys():
        save_path = "csv/" + str(element) + ".csv"
        # Set list of ignorable elements for less memory usage
        ignorable_elements = list(key_features.keys())
        ignorable_elements.remove(element)
        extract_entity(
            element,
            key_features[element],
            dblp_path,
            save_path,
            ignorable_elements=ignorable_elements,
        )


if __name__ == "__main__":
    main()
