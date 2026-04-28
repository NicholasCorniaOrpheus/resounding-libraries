"""
This script implements a named entity recognition of Koha Authorities on the transcribed texts imported from Transkribus.

1. Import PAGEXML transcript from Transkribus API, associated to a specific barcode -> biblioitem.
2. Convert the XML file in dictionary
3. Word-matching algorithm against list of Koha AUthorities.
4. Export result in marc-in-json format for each biblioitem.
5. Import new keywords in biblioitem.

"""

from rapidfuzz import fuzz, process
import re


def preprocess_dutch(text):
    """Normalize Dutch text for better matching. Made with Copilot"""
    # Convert to lowercase
    text = text.lower()
    # Remove common abbreviation periods
    text = re.sub(r"\.(?=\s|$)", "", text)
    # Normalize whitespace
    text = " ".join(text.split())
    return text


def match_with_threshold(
    query: str, filtered_auth: list, threshold=80, limit_results=20
) -> list:
    """Find matches above similarity threshold. Made with Copilot.
    Args:
    query (str): String to be matched with the authority main headings.
    filtered_auth (list): List of authorities to be matched with.
    threshold (int): Similarity threshold between 0-100.
    limit_results (int): Maximal number of results. Default is 20.

    Returns:
    matches (list): List of matches of the form (m_heading,similarity_score,auth_index)

    Examples:
    >>> word = "viool"
    >>> match_with_threshold(word,filtered_auth)
    >>>
    """

    query_clean = preprocess_dutch(query)

    # UNDERSTAND scoring systems: https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html

    # NOT WORKING PROPERLY!

    exact_matches = process.extract(
        query_clean,
        [preprocess_dutch(auth["m_heading"]) for auth in filtered_auth],
        scorer=fuzz.ratio,  # Exact match
        limit=limit_results,
        score_cutoff=threshold,
    )

    partial_matches = exact_matches = process.extract(
        query_clean,
        [preprocess_dutch(auth["m_heading"]) for auth in filtered_auth],
        scorer=fuzz.partial_ratio,  # Find word in sentence
        limit=limit_results,
        score_cutoff=threshold,
    )

    print(f"Exact matches: \n {exact_matches} \n Partial matches: {partial_matches}")


def get_authority_type(record: dict, auth_type_field=["942", "a"]) -> str:
    """
    This function returns the authority type code of a given record.

    Args:
    record (dict): MARC-in-JSON record of the authority, conform with Koha API.
    auth_type_field (list): MARC field holding the authority type code. Default is 942$a.


    Returns:
    auth_type (str): Authority type code.

    Examples:
    """
    try:
        # get authority type
        query_field = list(
            filter(lambda x: auth_type_field[0] in x.keys(), record["fields"])
        )
        # the field should be unique
        auth_type = list(
            filter(
                lambda x: auth_type_field[1] in x.keys(),
                query_field[0][auth_type_field[0]]["subfields"],
            )
        )[0]["a"]

        return auth_type

    except Exception:
        return None


def get_main_heading(
    record: dict,
    headings={
        "PERSO_NAME": "100",
        "CORPO_NAME": "110",
        "CHRON_TERM": "148",
        "TOPIC_TERM": "150",
        "GEOGR_NAME": "151",
        "KOOPM_KEYW": "150",
    },
    heading_subfield="a",
) -> str:
    """
    This function returns the authority main heading of a given record.

    Args:
    record (dict): MARC-in-JSON record of the authority, conform with Koha API.
    headings (dict): Dictionary of main heading fields according to authorty type. Default is {"PERSO_NAME": "100","CORPO_NAME": "110","CHRON_TERM": "148","TOPIC_TERM": "150","GEOGR_NAME": "151"}
    heading_subfield (str): Subfield of the main heading. Default is "a".


    Returns:
    main_heading (str): Main heading string.

    Examples:
    """
    # get authority type
    auth_type = get_authority_type(record)
    heading_field = headings[auth_type]

    # get main heading
    try:
        query_field = list(
            filter(lambda x: heading_field in x.keys(), record["fields"])
        )
        # the field should be unique
        main_heading = list(
            filter(
                lambda x: heading_subfield in x.keys(),
                query_field[0][heading_field]["subfields"],
            )
        )[0][heading_subfield]

        return main_heading

    except Exception:
        return None


def get_alternative_headings(
    record: dict,
    headings={
        "PERSO_NAME": "400",
        "CORPO_NAME": "410",
        "CHRON_TERM": "448",
        "TOPIC_TERM": "450",
        "GEOGR_NAME": "451",
        "KOOPM_KEYW": "450",
    },
    heading_subfield="a",
) -> list:
    """
    This function returns a list of alternative headings (equivalent terms, pseudonyms,...) of a given record.

    Args:
    record (dict): MARC-in-JSON record of the authority, conform with Koha API.
    headings (dict): Dictionary of main heading fields according to authorty type. Default is {"PERSO_NAME": "100","CORPO_NAME": "110","CHRON_TERM": "148","TOPIC_TERM": "150","GEOGR_NAME": "151"}
    heading_subfield (str): Subfield of the main heading. Default is "a".


    Returns:
    alternative_headings (list): List of alternative headings.

    Examples:
    """
    # get authority type
    auth_type = get_authority_type(record)
    heading_field = headings[auth_type]

    # get alternative headings
    alternative_headings = []
    try:
        query_field = list(
            filter(lambda x: heading_field in x.keys(), record["fields"])
        )
        for statement in query_field:
            alt_heading = list(
                filter(
                    lambda x: heading_subfield in x.keys(),
                    statement[heading_field]["subfields"],
                )
            )[0][heading_subfield]
            alternative_headings.append(alt_heading)

        return alternative_headings

    except Exception:
        return None


def get_umbrella_terms(
    record: dict,
    umbrella_fields={
        "PERSO_NAME": "500",
        "CORPO_NAME": "510",
        "CHRON_TERM": "548",
        "TOPIC_TERM": "550",
        "GEOGR_NAME": "551",
    },
    umbrella_subfields={"label": "a", "id": "9"},
) -> list:
    """
    This function returns a list of umbrella terms of a given record.

    Args:
    record (dict): MARC-in-JSON record of the authority, conform with Koha API.
    umbrella_fields (dict): Dictionary of umbrella fields for the authority type, according to MARC21 guidelines.
    umbrella_subfields (str): label and authority id for each umbrella term. Default is {"label": "a","id": "9"}.


    Returns:
    umbrella_terms (list): List of umbrella terms.

    Examples:
    """
    # get umbrella terms
    umbrella_terms = []
    try:
        for auth_type in umbrella_fields.keys():
            query_field = list(
                filter(
                    lambda x: umbrella_fields[auth_type] in x.keys(), record["fields"]
                )
            )
            for statement in query_field:
                umbrella_term = {"type": auth_type}
                for umbrella_key in umbrella_subfields.keys():
                    metadata = list(
                        filter(
                            lambda x: umbrella_subfields[umbrella_key] in x.keys(),
                            statement[umbrella_fields[auth_type]]["subfields"],
                        )
                    )
                    if len(metadata) > 0:
                        umbrella_term[umbrella_key] = metadata[0][
                            umbrella_subfields[umbrella_key]
                        ]
                    else:
                        metadata = None

                umbrella_terms.append(umbrella_term)

        return umbrella_terms

    except Exception:
        return None


def get_wikidata_entities(
    record: dict, wikidata_field="024", wikidata_subfields={"uri": "1", "label": "9"}
) -> list:
    """
    This function returns a list of wikidata entities linked with a given record.

    Args:
                                                    record (dict): MARC-in-JSON record of the authority, conform with Koha API.
                                                    wikidata_field (str): Default is "024", according to MARC21 guidelines.
                                                    wikidata_subfields (str): label and authority id for each umbrella term. Default is {"label": "a","id": "9"}.


    Returns:
                                                    wikidata_entities (list): List of Wikidata entities.

    Examples:
    """
    # get wikidata entities
    wd_entities = []
    try:
        query_field = list(
            filter(lambda x: wikidata_field in x.keys(), record["fields"])
        )
        for statement in query_field:
            wikidata_entity = {}
            for wikidata_key in wikidata_subfields.keys():
                metadata = list(
                    filter(
                        lambda x: wikidata_subfields[wikidata_key] in x.keys(),
                        statement[wikidata_field]["subfields"],
                    )
                )
                if len(metadata) > 0:
                    subfield = wikidata_subfields[wikidata_key]
                    wikidata_entity[wikidata_key] = metadata[0][subfield]
                else:
                    metadata = None

            wd_entities.append(wikidata_entity)

        return wd_entities

    except Exception:
        return None


def import_koha_authorities(
    auth_dict: dict,
    auth_types=["KOOPM_KEYW"],
    auth_type_field=["942", "a"],
    headings={
        "PERSO_NAME": "100",
        "CORPO_NAME": "110",
        "CHRON_TERM": "148",
        "TOPIC_TERM": "150",
        "GEOGR_NAME": "151",
        "KOOPM_KEYW": "150",
    },
) -> dict:
    """
    This function imports the Koha Authorities from a given dictionary and filters them based on specified authority types and fields.

    Args:
    auth_dict (dict): A marc-in-json dictionary containing the Koha Authorities of the form {"auth_id": auth_id, "wd_id": wd_id, "record": {"leader": ... , "fields": [...]}}
    auth_types (list): A list of authority types to filter by. Default is ["KOOPM_KEYW"].
    auth_types_field (list): A list of fields to filter by. Default is ["942","a"].
    headings (dict): Dictionary of main headings fields to be used to matching

    Returns:
    dict: A condensed dictionary of authorities for the word-matching algorithm.

    Examples:

    """
    filtered_auths = []

    for auth in auth_dict:
        auth_type = get_authority_type(auth["record"], auth_type_field=auth_type_field)
        if auth_type in auth_types:
            filtered_auths.append(
                {
                    "auth_id": auth["auth_id"],
                    "auth_type": auth_type,
                    "m_heading": get_main_heading(auth["record"]),
                    "alt_heading": get_alternative_headings(auth["record"]),
                    "umbrella_terms": get_umbrella_terms(auth["record"]),
                    "wd_entities": get_wikidata_entities(auth["record"]),
                }
            )

    return filtered_auths
