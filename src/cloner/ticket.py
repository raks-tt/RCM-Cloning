"""Module to work with Jira tickets."""

import logging
import re
import requests

from requests_kerberos import HTTPKerberosAuth, DISABLED
from urllib import urlencode

from ticketutil.jira import JiraTicket
from ticketutil.ticket import _get_kerberos_principal

PROD_URL = 'https://projects.engineering.redhat.com'
STAGE_URL = 'https://projects.stage.engineering.redhat.com'
PROD_KEYWORDS_ID = 'customfield_12407'
STAGE_KEYWORDS_ID = 'customfield_12700'


def substitute_pav(ticketobj):
    """Callback handler for substituting <PAV>.
    Preferred is usage of single value per cloned template.

    Args:
       ticketobj: instance of Ticket

    Returns:
        ', ' joined list of PAV (works with multiple)
    """
    result = None
    if ticketobj.pav:
        result = ", ".join(ticketobj.pav)
        logging.debug("substituting <PAV> with '{0}'".format(result))
    return result


def substitute_keywords(ticketobj):
    """Callback handler for substituting <KEYWORD>.
    Preferred is usage of single value per cloned template.

    Args:
       ticketobj: instance of Ticket

    Returns:
        ', ' joined list of keywords (works with multiple)
    """
    result = None

    if ticketobj.keywords:
        print ticketobj.keywords
        result = ", ".join(ticketobj.keywords)
        logging.debug("substituting <KEYWORK> with '{0}'".format(result))
    return result


def substitute_milestone(ticketobj):
    """Callback handler for substituting <MILESTONE>.
    Preferred is usage of single value per cloned template.

    Args:
       ticketobj: instance of Ticket

    Returns:
        ', ' joined list of milestones (works with multiple).
    """
    result = None
    if ticketobj.milestone:
        result = ", ".join(ticketobj.milestone)
        logging.debug("substituting <MILESTONE> with '{0}'".format(result))
    return result


def substitute_custom_text(ticketobj):
    """Callback handler for substituting <CUSTOM_TEXT>

    Args:
       ticketobj: instance of Ticket

    Returns:
        returns ticketobj.custom_substitutions['CUSTOM_TEXT']
    """
    result = None
    if "CUSTOM_TEXT" in ticketobj.custom_substitutions.keys():
        result = ticketobj.custom_substitutions["CUSTOM_TEXT"]
        logging.debug("substituting <CUSTOM_TEXT> with '{0}'".format(result))
    return result


SUPPORTED_VAR_SUBSTITUTIONS = {
    r'<PAV>': substitute_pav,
    r'<CUSTOM_TEXT>': substitute_custom_text,
    r'<KEYWORD>': substitute_keywords,
    r'<MILESTONE>': substitute_milestone,
}


class Ticket(JiraTicket):
    """Object representation of a JIRA Ticket."""

    def __init__(self, prod=False, project='RCMTEMPL', auth=None,
                 ticket_id=None, custom_substitutions=None):
        url = PROD_URL if prod else STAGE_URL
        self.keywords_id = PROD_KEYWORDS_ID if prod else STAGE_KEYWORDS_ID
        super(Ticket, self).__init__(url, project, auth=auth,
                                     ticket_id=ticket_id)
        self._user = None
        self.custom_substitutions = custom_substitutions
        if self.ticket_id:
            self._content = self._get_content()
        else:
            self._content = None

    @property
    def custom_substitutions(self):
        """Return custom_substitutions value. See e.g <CUSTOM_TEXT>"""
        logging.debug(
            "Getting .custom_substitutions {0}".format(
                self._custom_substitutions
            )
        )
        return self._custom_substitutions

    @custom_substitutions.setter
    def custom_substitutions(self, val):
        """
        Accepts:
            Dict {'key': 'value'} - dict is used to pass user defined values
            these values are then used in get_substituted_string() and handled
            via substitute_* callbacks above
        """
        if not val:
            val = {}
        assert isinstance(val, dict), "Expected dict instance on input."
        logging.debug("Setting .custom_substitutions to '{0}'".format(val))
        self._custom_substitutions = val

    @property
    def content(self):
        """Return dictionary with content of the ticket."""
        return self._content

    @content.setter
    def content(self, val):
        self._content = val

    @property
    def summary(self):
        """Return ticket summary."""
        if self.content:
            return self.content['fields']['summary']

    @summary.setter
    def summary(self, val):
        self.content['fields']['summary'] = val

    @property
    def description(self):
        """Return ticket description."""
        if self.content:
            return self.content['fields']['description']

    @description.setter
    def description(self, val):
        self.content['fields']['description'] = val

    @property
    def issuetype(self):
        """Return ticket type."""
        if self.content:
            return self.content['fields']['issuetype']['name']

    @property
    def pav(self):
        """Return Product Affects Version field."""
        if self.content and 'customfield_11911' in self.content['fields']:
            pav = self.content['fields']['customfield_11911']
            if pav:
                return [item.get('value') for item in pav]
        return []

    def add_pav(self, val):
        """Add pav to ticket (without touching other pavs in ticket).

        Args:
            val: PAV to be added as string

        Returns:
            self.requests_result, named tuple containing request status,
            error_message and url info
        """
        payload = {"update": {
            "customfield_11911": [{"add": {"value": val}}]}}
        url = '{0}/{1}'.format(self.rest_url, self.ticket_id)
        try:
            r = self.s.put(url, json=payload)
            logging.debug('Append PAV: Status code {0}'.format(r.status_code))
            r.raise_for_status()
            return self.request_result
        except requests.RequestException as e:
            error_message = "Error appending PAV"
            logging.error(error_message)
            logging.error(e)
            return self.request_result._replace(status='Failure',
                                                error_message=error_message)

    @property
    def keywords(self):
        """Return keywords field."""
        if self.content and 'customfield_12700' in self.content['fields']:
            keywords = self.content['fields']['customfield_12700']
            return [item.get('value') for item in keywords]
        return []

    @property
    def milestone(self):
        """Return milestone field."""
        if self.content and 'customfield_12000' in self.content['fields']:
            milestone = self.content['fields']['customfield_12000']
            return [item.get('value') for item in milestone]
        return []

    @property
    def labels(self):
        """Return ticket labels."""
        if self.content:
            return self.content['fields']['labels']

    @property
    def parent_id(self):
        """Return parent's ID if issue type is Sub-task, else is None."""
        if (self.content is not None and
            self.issuetype == 'Sub-task' and
                self.content['fields']['parent']['key'].startswith(
                    'RCMTEMPL')):
            return self.content['fields']['parent']['key']

    @property
    def subtask_ids(self):
        """Return list of subtask IDs that are in RCMTEMPL."""
        if self.content is not None:
            subtasks = self.content['fields']['subtasks']
            if subtasks:
                ids = []
                for subtask in subtasks:
                    if subtask['key'].startswith('RCMTEMPL'):
                        ids.append(subtask['key'])
                return ids
        return []

    @property
    def nr_of_subtasks(self):
        """Return number of all subtasks (not only in RCMTEMPL)."""
        if self.content is not None and self.issuetype != 'Sub-task':
            return len(self.content['fields']['subtasks'])

    @property
    def links(self):
        """Return list of tuples (ID, type, 'inwardIssue'/'outwardIssue') that
        describe ticket links.

        Links of type 'Cloners' and 'Duplicate 'or links to projects other than
        'RCMTEMPL' are disregarded.
        Links are not retrieved for subtasks until DEVOPSA-2207 is resolved.
        """
        if self.issuetype == 'Sub-task':
            return []
        issuelinks = self.content['fields']['issuelinks']
        links = []
        if self.content is not None and issuelinks:
            for link in issuelinks:
                relation = 'inwardIssue' if link.get('inwardIssue') \
                    else 'outwardIssue'
                task_id = link[relation]['key']
                link_type = link['type']['name']
                if link_type in ['Cloners', 'Duplicate']:
                    logging.debug('Not cloning {0} linked to {1}, it is '
                                  'unsupported type {2}.'.format(
                                      task_id, self.ticket_id, link_type))
                    continue
                if not task_id.startswith('RCMTEMPL-'):
                    logging.debug('Not cloning {0} linked to {1}, it is not in'
                                  ' RCMTEMPL.'.format(task_id, self.ticket_id))
                    continue
                links.append((task_id, link_type, relation))
        return links

    def get_substituted_string(self, field):
        """Update field of ticket with supported substitutions
        See SUPPORTED_VAR_SUBSTITUTIONS.
        Function prints warning if value is not set.
        In this case string is not substituted.

        Return field value with substituted variables
        """
        result = field
        for regex, callback in SUPPORTED_VAR_SUBSTITUTIONS.iteritems():
            logging.debug(
                u"Searching for regex '{0}' in {1}".format(regex, result)
            )
            if re.search(regex, field):
                logging.debug(u"Matched regex '{0}'.".format(result))
                subst_with = callback(self)
                if not subst_with:
                    logging.warning(
                        u"Not substituting '{0}' got None. ".format(regex))
                    logging.warning(
                        u"Fields: {0}".format(self.content['fields']))
                    continue
                result = re.sub(regex, subst_with, result)
            else:
                logging.debug(u"Did not match regex '{0}'.".format(regex))

        return result

    def create_link(self, link):
        """Create issue link.

        Args:
            link: Tuple in format (ID, type, 'inwardIssue'/'outwardIssue')

        Returns:
            In case of failure namedtuple with status, error message and url,
            else Non
        """
        link_id, link_type, direction = link
        inward = self.ticket_id if direction == 'outwardIssue' else link_id
        outward = self.ticket_id if direction == 'inwardIssue' else link_id
        payload = {
            "type": {
                "name": link_type
            },
            "inwardIssue": {
                "key": inward
            },
            "outwardIssue": {
                "key": outward
            }
        }
        url = '{0}Link'.format(self.rest_url)
        try:
            r = self.s.post(url, json=payload)
            logging.debug('Create issue link: Status code {0}'.format(
                r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            error_message = "Error while creating issue link - {0}".format(
                r.json()['errorMessages'][0])
            logging.error(error_message)
            logging.error(e)
            return self.request_result._replace(status='Failure',
                                                error_message=error_message
                                                )

    @property
    def remote_links(self):
        """Return dictionary with representation of remote links if ticket has
        any, else None.
        """
        remote_links = self._get_remote_links()
        if (hasattr(remote_links, 'status') and
                remote_links.status == 'Failure'):
            return
        return remote_links

    def _get_remote_links(self):
        """Get dictionary with remote links.

        Returns:
            Dictionary with representation of remote links if successful,
            else named tuple with status, error message and url
        """
        url = '{0}/{1}/remotelink'.format(self.rest_url, self.ticket_id)
        try:
            r = self.s.get(url)
            logging.debug('Get ticket content: Status code {0}'.format(
                r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            error_message = "Error while getting ticket remote links"
            logging.error(error_message)
            logging.error(e)
            return self.request_result._replace(status='Failure',
                                                error_message=error_message)
        return r.json()

    def create_remote_link(self, links):
        """Create remote links from list of dictionaries.

        First removes fields 'id' and 'self' because they should not be cloned.

        Args:
            links: List of dictionaries with representation of links

        Returns:
            In case of failure namedtuple with status, error message and url,
            else None
        """
        for link in links:
            link.pop("id")
            link.pop("self")
            url = '{0}/{1}/remotelink'.format(self.rest_url, self.ticket_id)
            try:
                r = self.s.post(url, json=link)
                logging.debug('Create remote link: Status code {0}'.format(
                    r.status_code))
                r.raise_for_status()
            except requests.RequestException as e:
                error_message = "Error creating remote ticket link - {0}".\
                    format(r.json()['errorMessages'][0])
                logging.error(error_message)
                logging.error(e)
                return self.request_result._replace(status='Failure',
                                                    error_message=error_message
                                                    )

    @property
    def status(self):
        """Return ticket status as a string, if no content returns None."""
        if self.content is not None:
            return self.content['fields']['status']['name']

    def _get_content(self):
        """Get content of a JIRA ticket.

        Returns:
            Dictionary containing ticket fields
        """
        self.s.headers.update({'Content-Type': 'application/json'})
        url = '{0}/{1}'.format(self.rest_url, self.ticket_id)
        r = self.s.get(url)
        logging.debug('Get ticket content: Status code {0}'.format(
            r.status_code))
        r.raise_for_status()
        return r.json()

    @property
    def user(self):
        """Return username of currently logged in user."""
        if not self._user:
            self._user = self._get_currently_logged_in_user()
        return self._user

    def _get_currently_logged_in_user(self):
        """Get the username of currently logged in user.

        Returns:
            Username of the currently logged in user
        """
        url = '{0}/rest/auth/1/session'.format(self.url)
        r = self.s.get(url)
        logging.debug(
            "Getting current user's username: Status code {0}".format(
                r.status_code))
        r.raise_for_status()
        return r.json()['name']

    def clone(self, other, inject=None, custom_substitutions=None,
              parent=None):
        """Clone other ticket to new one.

        Args:
            other: Ticket object from which we clone data.
            inject: Dictionary with fields to be injected into content
            parent: In case of subtask, specifies its parent's ID
        """
        self.content = {"fields": other.content['fields'].copy()}
        self.remove_unwanted_fields()
        self.remove_customfields()
        self.fix_specific_fields()
        self.content['fields']['project'] = {'key': self.project}
        self.content['fields']['reporter'] = {'name': self.user}
        self.content['fields']['assignee'] = {'name': self.user}
        if parent:
            self.content['fields'].update({'parent': {'key': parent}})
        if inject is not None:
            self.content['fields'].update(inject)
        # this needs to be executed before substitution
        self.custom_substitutions = custom_substitutions

        # substitution must be executed after inject part
        self.substitute_fields()
        self.create_from_json(self.content)
        if other.remote_links:
            self.create_remote_link(other.remote_links)

    def substitute_fields(self):
        """Substitute text in supported fields.
        Currently limited to summary and description
        """
        self.summary = self.get_substituted_string(self.summary)
        self.description = self.get_substituted_string(self.description)

    def create_from_json(self, json):
        """Create ticket from json.

        Args:
            json: Json dictionary with ticket data
        """
        return self._create_ticket_request(json)

    def verify_position(self, position):
        """Ask user if they want to continue if the position is invalid.

        Args:
            position: Desired zero-indexed final position of a subtask as int
        """
        last_position = self.nr_of_subtasks - 1
        if position is None or position > last_position or position < 0:
            is_valid = False
            while not is_valid:
                input = raw_input(
                    'WARNING: Position is not specified or invalid, '
                    'Subtask clone will be positioned at the end.\n'
                    'Are you sure you would like to continue? (Y/N) ')
                if input in ['y', 'n', 'Y', 'N']:
                    is_valid = True
                else:
                    logging.error('Unexpected value provided, try again.')
            if input.lower() == 'y':
                return
            else:
                logging.info('Exiting. No changes were made.')
                raise SystemExit()

    def change_subtask_position(self, position):
        """Move subtask from last position to desired_position.

        Works only if ticket has subtasks.

        Args:
            position: Desired zero-indexed final position of a subtask as int
        """
        if self.issuetype == 'Sub-task' or not self.nr_of_subtasks:
            return
        internal_jira_id = self.content.get('id')
        last_position = self.nr_of_subtasks - 1
        if position > last_position or position < 0:
            logging.warning('Position of the cloned subtask was not provided '
                            'or invalid, cloned subtask will be at the end of '
                            'the subtask list')
            return
        url = '{0}/secure/MoveIssueLink.jspa?id={1}&currentSubTaskSequence=' \
              '{2}&subTaskSequence={3}'.format(self.url, internal_jira_id,
                                               last_position, position)
        r = self.s.get(url)
        logging.debug('Changing subtask position: Status code: {0}'.format(
            r.status_code))
        r.raise_for_status()

    def search(self, query):
        """Search in JIRA using jql.

        Args:
            query: JQL query to search
        Returns:
            List of ticket IDs that match given query
        """
        jql = urlencode({
            'jql': '{0}'.format(query),
            'fields': 'key',
            'maxResults': '500'})
        try:
            r = self.s.get('{0}/rest/api/2/search?{1}'.format(self.url, jql))
            logging.debug('Search for tickets: Status code {0}'.format(
                r.status_code))
            r.raise_for_status()
        except requests.RequestException:
            error_message = 'Error while performing search - {0}'.format(
                r.json()['errorMessages'][0])
            logging.error(error_message)
            return self.request_result._replace(status='Failure',
                                                error_message=error_message)
        id_list = [d.get('key') for d in r.json()['issues']]
        return id_list

    def remove_unwanted_fields(self):
        """Remove empty or undesired fields.

        Empty fields are those that are None, unwanted fields are those that
        cannot be copied from RCMTEMPL project to other because they are
        specific to that project or copying doesn't make sense (e.g. creator).

        TODO solve issuelinks when working on DEVOPSA-1939
        """
        unwanted = ['aggregatetimeoriginalestimate', 'timetracking',
                    'timeestimate', 'progress', 'aggregateprogress',
                    'timeoriginalestimate', 'aggregatetimeestimate',
                    'worklog', 'workratio', 'updated', 'created', 'creator',
                    'watches', 'votes', 'issuelinks', 'comment', 'status',
                    'lastViewed', 'reporter', 'parent', 'subtasks',
                    'aggregatetimespent', 'timespent']
        for key, val in list(self.content['fields'].items()):
            if not val or key in unwanted:
                self.content['fields'].pop(key, None)

    def fix_specific_fields(self):
        """Fix values for specific fields that cannot be cloned.

        Some fields are dict type themselves but we cannot copy all of the
        values because then JIRA has problem with internal IDs, so we copy
        just the value.
        """
        # ticket fields that are represented by dicts
        fields_as_dicts = ['issuetype', 'priority']
        # ticket fields that are represented by list of dicts
        fields_as_list_of_dicts_value = [self.keywords_id]
        fields_as_list_of_dicts_name = ['components']
        fields = self.content['fields']
        for key in list(fields.keys()):
            if key in fields_as_dicts:
                # in dict remove all fields but "name"
                fields[key] = {"name": fields[key].get("name")}
            elif key in fields_as_list_of_dicts_value:
                # remove all fields but "value" in each dict in list
                fields[key] = [{"value": item.get("value")} for item in
                               fields[key]]
            elif key in fields_as_list_of_dicts_name:
                # remove all fields but "name" in each dict in list
                fields[key] = [{"name": item.get("name")} for item in
                               fields[key]]

    def remove_customfields(self):
        """Remove invalid custom fields.

        JIRA provides in its API responses customfields that are not set up for
        specific projects but all customfields in general. These have to be
        removed and only the valid ones can be left.
        """
        valid = ['customfield_12200', 'customfield_10006', 'customfield_11911',
                 'customfield_11910', 'customfield_12000', 'customfield_12001',
                 'customfield_12002', 'customfield_10400', 'customfield_10005',
                 'customfield_10002', self.keywords_id]
        for key in list(self.content['fields'].keys()):
            if key.startswith('customfield_') and key not in valid:
                self.content['fields'].pop(key)

    def _create_requests_session(self):
        """Overridden method from ticketutil to be less "noisy"."""
        s = requests.Session()
        if self.auth == 'kerberos':
            self.principal = _get_kerberos_principal()
            s.auth = HTTPKerberosAuth(mutual_authentication=DISABLED)
            s.verify = False
        if isinstance(self.auth, tuple):
            s.auth = self.auth
        try:
            r = s.get(self.auth_url)
            logging.debug("Create requests session: status code: {0}".format(
                r.status_code))
            r.raise_for_status()
            return s
        except requests.RequestException as e:
            logging.error("Error authenticating to {0}".format(self.auth_url))
            logging.error(e)
            s.close()

    def add_comment(self, comment):
        """Override method from ticketutil to be less "noisy"."""
        logging.disable(logging.INFO)
        super(Ticket, self).add_comment(comment)
        logging.disable(logging.NOTSET)
