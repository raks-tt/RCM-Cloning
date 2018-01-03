from ticket import Ticket


def prepare_inject(fields, prod=False):
    """Create properly formatted dictionary and remove invalid entries from
    passed fields.

    Args:
        fields: Fields dictionary
        prod: Bool value to choose if production JIRA is used, default False

    Returns:
        Dictionary with supported fields properly formatted for JIRA API
    """
    valid_fields = {}
    for key, val in list(fields.items()):
        if key == 'PAV':
            valid_fields["customfield_11911"] = [{"value": val}]
            continue
        if key == 'keywords':
            keywords_id = "customfield_12407" if prod else "customfield_12700"
            valid_fields[keywords_id] = [{"value": keyword}
                                         for keyword in val]
            continue
        if key == 'labels':
            valid_fields[key] = val
            continue
        if key == 'assignee':
            valid_fields[key] = {"name": val}
            continue
        if key == 'reporter':
            valid_fields[key] = {"name": val}
            continue
        if key == 'milestone':
            valid_fields["customfield_12000"] = [{"value": val}]
            continue
    return valid_fields


def get_ticket_IDs_specific(pav, keywords=None, prod=False):
    """Get list of tickets from RCMTEMPL project based on passed parameters
    with specific restrictions for searching.

    If keywords are specified, they don't apply to subtasks.

    Args:
        pav: Product Affects Version field as string
        keywords: List of string keywords, default None
        prod: Bool value to choose if production JIRA is used, default True

    Returns:
        List of string ticket IDs that match passed parameters
    """
    query = 'project=RCMTEMPL and "Product Affects Version"="{0}"'.format(pav)
    if keywords:
        query += ' and ((issuetype="Sub-task") or (issuetype!="Sub-task"'
        for item in keywords:
            query += ' and "Keyword"="{0}"'.format(item)
        query += '))'
    # create dummy ticket to search with
    t = Ticket(prod=prod)
    tickets = t.search(query)
    return tickets


def get_ticket_IDs(prod=True, pav=None, keywords=None):
    """Get list of tickets from RCMTEMPL project based on passed parameters.
    Only parameters 'Product Affects Version' and 'Keyword' supported.

    Args:
        prod: bool value to choose if production JIRA is used, default True
        pav: Product Affects Version field as string, default None
        keywords: List of string keywords, default None

    Returns:
        List of string ticket IDs that match passed parameters
    """
    query = 'project=RCMTEMPL'
    if pav:
        query += ' and "Product Affects Version"="{0}"'.format(pav)
    if keywords:
        for item in keywords:
            query += ' and "Keyword"="{0}"'.format(item)
    # create dummy ticket to search with
    t = Ticket(prod=prod)
    tickets = t.search(query)
    return tickets
