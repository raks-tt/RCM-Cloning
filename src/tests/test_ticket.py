import json
import logging
import requests
import unittest

from mock import MagicMock, patch

from cloner.ticket import Ticket


def open_fake_task_content():
    with open('tests/fake_task_content.json') as f:
        return json.load(f)


def open_fake_subtask_content():
    with open('tests/fake_subtask_content.json') as f:
        return json.load(f)

FAKE_SEARCH_CONTENT = {
    "issues": [
        {"key": "ISSUE-1"},
        {"key": "ISSUE-2"}
    ]
}

FAKE_SEARCH_ERROR = {
    "errorMessages": [
        "This is and ex-parrot!"
    ],
    "errors": {}
}

FAKE_REMOTE_LINKS = [
    {
        "application": {},
        "self": "https://projects.stage.engineering.redhat.com/rest/api/2/issue/RCMTES-37/remotelink/26101",  # noqa
        "object": {
            "url": "https://docs.google.com/a/redhat.com/document/d/1dVK0ObhIzMrE4guINFLu_ukwwDMJP-Sx6hhhBEXdzxk/edit?usp=sharing",  # noqa
            "status": {
                "icon": {}
            },
            "icon": {
                "url16x16": "https://docs.google.com/favicon.ico"
            },
            "title": "First Week New Hire Orientation"
        },
        "id": 26101
    },
    {
        "application": {},
        "self": "https://projects.stage.engineering.redhat.com/rest/api/2/issue/RCMTES-37/remotelink/26200",  # noqa
        "object": {
            "url": "http://https://developer.atlassian.com/jiradev/jira-platform/guides/other/guide-jira-remote-issue-links/jira-rest-api-for-remote-issue-links",  # noqa
            "status": {
                "icon": {}
            },
            "icon": {
                "url16x16": ""
            },
            "title": "JIRA api"
        },
        "id": 26200
    }
]


class FakeResponse(object):
    """Mock response coming from server via Requests."""

    def __init__(self, status_code=666, search=False, subtask=False,
                 remote_links=False):
        self.status_code = status_code
        self.search = search
        self.subtask = subtask
        self.remote_links = remote_links

    def raise_for_status(self):
        if self.status_code != 666:
            raise requests.RequestException

    def json(self):
        """Return json-like mock result of the REST API query."""
        if self.search:
            if self.status_code == 666:
                return FAKE_SEARCH_CONTENT
            else:
                return FAKE_SEARCH_ERROR
        elif self.remote_links:
            return FAKE_REMOTE_LINKS
        else:
            if self.subtask:
                return open_fake_subtask_content()
            else:
                return open_fake_task_content()


class FakeSession(object):
    """Mock Requests session behavior."""

    def __init__(self, status_code=666, search=False, subtask=False,
                 remote_links=False):
        self.status_code = status_code
        self.search = search
        self.subtask = subtask
        self.remote_links = remote_links
        self.headers = {'Content-Type': 'application/json', }

    def get(self, url):
        if self.search:
            return FakeResponse(status_code=self.status_code,
                                search=self.search)
        elif self.remote_links:
            return FakeResponse(status_code=self.status_code,
                                remote_links=True)
        else:
            return FakeResponse(status_code=self.status_code,
                                subtask=self.subtask)


class TestTaskTicket(unittest.TestCase):
    """Test methods and properties of Task ticket."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.patcher = patch('cloner.ticket.Ticket._create_requests_session')
        mock_session = self.patcher.start()
        mock_session.return_value = FakeSession()
        self.t = Ticket(ticket_id='ID-1')
        self.substitued_t = Ticket(ticket_id='ID-1')
        self.substitued_t.substitute_fields()

    def tearDown(self):
        self.patcher.stop()

    def test_get_content(self):
        """Test that content gets set during initialization."""
        self.assertEqual(self.t.content, open_fake_task_content())

    def test_get_summary(self):
        """Test that getting summary works."""
        # PAV in fake data is ["amq-clients-1.0", "ansible-tower-3.0"]
        self.assertEqual(self.substitued_t.summary,
                         "%s rcm-pdc: ensure that PRUNED staging dir for Supplementary compose was created" % ", ".join(["amq-clients-1.0", "ansible-tower-3.0"]))  # noqa

    def test_get_issuetype(self):
        """Test that getting issuetype works."""
        self.assertEqual(self.t.issuetype, 'Task')

    def test_get_pav(self):
        """Test that getting pav works."""
        self.assertEqual(self.t.pav, ["amq-clients-1.0", "ansible-tower-3.0"])

    def test_get_labels(self):
        """Test that getting labels works."""
        self.assertEqual(self.t.labels, ["NEW", "bug"])

    def test_get_parent(self):
        """Test that getting parent of a task returns None."""
        self.assertIsNone(open_fake_task_content()['fields'].get('parent'))

    def test_get_subtasks(self):
        """Test that getting subtasks only from RCMTEMPL works."""
        expected = ['RCMTEMPL-666']
        self.assertEqual(self.t.subtask_ids, expected)

    def test_get_nr_of_subtasks(self):
        """Test that getting number of subtasks works with all projects."""
        self.assertEqual(self.t.nr_of_subtasks, 2)

    def test_get_links(self):
        """Test that getting links returns only those we want."""
        self.assertEqual(self.t.links,
                         [('RCMTEMPL-23', 'Blocks', 'outwardIssue')])

    def test_get_status(self):
        """Test that property status is returned from content."""
        self.assertEqual(self.t.status,
                         open_fake_task_content()['fields']['status']['name'])

    @patch('cloner.ticket.raw_input')
    @patch('cloner.ticket.Ticket.create_from_json')
    @patch('cloner.ticket.Ticket.create_remote_link')
    def test_clone(self, mock_create_links, mock_create_ticket, mock_input):
        """Test that clone() calls create and required fields are copied."""
        t2 = Ticket(ticket_id='ID-2')
        t2._user = 'anon'
        mock_input.return_value = 'Y'
        t2.clone(self.t)
        mock_create_ticket.assert_called()
        mock_create_links.assert_called()
        self.assertEqual(self.substitued_t.content['fields'].get('summary'),
                         t2.content['fields'].get('summary'))
        self.assertEqual(self.substitued_t.content['fields'].get('description'),
                         t2.content['fields'].get('description'))

    @patch('cloner.ticket.raw_input')
    @patch('cloner.ticket.Ticket.create_from_json')
    @patch('cloner.ticket.Ticket.create_remote_link')
    def test_clone_with_inject(self, mock_create_links, mock_create_ticket,
                               mock_input):
        """Test that create() is called and fields are copied and injected."""
        t2 = Ticket(ticket_id='ID-2')
        t2._user = 'anon'
        injected = {"eggs": "good", "spam": "bad"}
        mock_input.return_value = 'Y'
        t2.clone(self.t, inject=injected)
        mock_create_ticket.assert_called()
        mock_create_links.assert_called()
        self.assertEqual(self.substitued_t.content['fields'].get('summary'),
                         t2.content['fields'].get('summary'))
        self.assertEqual(self.substitued_t.content['fields'].get('description'),
                         t2.content['fields'].get('description'))
        self.assertDictContainsSubset(injected, t2.content['fields'])

    @patch('cloner.ticket.Ticket.create_from_json')
    def test_create_from_json(self, mock_create):
        """Test that create_from_json() calls creating method."""
        self.t.create_from_json({"data": "some data"})
        mock_create.assert_called_with({"data": "some data"})

    def test_remove_unwanted_fields(self):
        """Test that method removes all unwanted fields."""
        unwanted = ['aggregatetimeoriginalestimate', 'timetracking',
                    'timeestimate', 'progress', 'aggregateprogress',
                    'timeoriginalestimate', 'aggregatetimeestimate',
                    'worklog', 'workratio', 'updated', 'created', 'creator',
                    'watches', 'votes', 'issuelinks', 'comment', 'status',
                    'lastViewed', 'reporter', 'aggregatetimespent',
                    'timespent']
        self.t.remove_unwanted_fields()
        for key in self.t.content['fields']:
            self.assertNotIn(key, unwanted)

    def test_fix_specific_fields(self):
        """Test that method fixes specific fields to only contain 'name'."""
        dicts = ['issuetype', 'priority']
        list_of_dicts_value = ['customfield_12700']
        list_of_dicts_name = ['components']
        self.t.fix_specific_fields()
        for key in self.t.content['fields']:
            if key in dicts:
                self.assertEqual(list(self.t.content['fields'][key].keys()),
                                 ["name"])
            elif key in list_of_dicts_value:
                self.assertEqual(self.t.content['fields'][key],
                                 [{"value": "Brew"}, {"value": "dist-git"}])
            elif key in list_of_dicts_name:
                self.assertEqual(self.t.content['fields'][key],
                                 [{"name": "BRMS"}])

    def test_remove_customfields(self):
        """Test that all customfields but valid are removed."""
        valid = ['customfield_12200', 'customfield_10006', 'customfield_11911',
                 'customfield_11910', 'customfield_12000', 'customfield_12001',
                 'customfield_12002', 'customfield_10400', 'customfield_10005',
                 'customfield_10002', 'customfield_12700']
        self.t.remove_customfields()
        self.assertNotEqual(len(self.t.content['fields']), 0)
        for key in self.t.content['fields']:
            if key.startswith('cusomfield_'):
                self.assertIn(key, valid)


class TestSubTaskTicket(unittest.TestCase):
    """Test methods and properties specific to subtasks (e.g. parent)."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.patcher = patch('cloner.ticket.Ticket._create_requests_session')
        self.mock_session = self.patcher.start()
        self.mock_session.return_value = FakeSession(subtask=True)
        self.t = Ticket(ticket_id='ID-1')

    def tearDown(self):
        self.patcher.stop()

    def test_get_content(self):
        """Test that content gets set during initialization."""
        self.assertEqual(self.t.content, open_fake_subtask_content())

    def test_get_issuetype(self):
        """Test that getting issuetype works."""
        self.assertEqual(self.t.issuetype, 'Sub-task')

    def test_get_parent(self):
        """Test that getting parent of a subtask works."""
        self.assertEqual(self.t.parent_id,
                         open_fake_subtask_content()['fields']['parent']['key']
                         )

    def test_get_subtask(self):
        """Test that getting subtasks of a subtasks returns None."""
        self.assertEqual(self.t.subtask_ids, [])

    def test_get_nr_of_subtasks(self):
        """Test that getting number of subtasks of a subtasks returns None."""
        self.assertIsNone(self.t.nr_of_subtasks)

    def test_get_links(self):
        """Test that no links are retrieved for subtasks."""
        self.assertEqual(self.t.links, [])


class TestTicketSearch(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)

    @patch('cloner.ticket.Ticket._create_requests_session')
    def test_search_with_valid_query(self, mock_session):
        """Test that search returns results with valid query."""
        mock_session.return_value = FakeSession(search=True)
        t = Ticket()
        self.assertEqual(['ISSUE-1', 'ISSUE-2'], t.search('valid'))

    @patch('cloner.ticket.Ticket._create_requests_session')
    @patch('cloner.ticket.Ticket._verify_project')
    def test_search_with_invalid_query(self, mock_verify, mock_session):
        """Test that search returns None and raises with invalid query."""
        mock_verify.return_value = True
        mock_session.return_value = FakeSession(status_code=404, search=True)
        t = Ticket()
        result = t.search('invalid')
        self.assertEqual('Failure', result.status)


class TestTicketRemoteLinks(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)

    @patch('cloner.ticket.Ticket._create_requests_session')
    def test_get_remote_links(self, mock_session):
        """Test that remote links work as expected."""
        mock_session.return_value = FakeSession(remote_links=True)
        t = Ticket()
        self.assertEqual(t.remote_links, FAKE_REMOTE_LINKS)

    @patch('cloner.ticket.Ticket._create_requests_session')
    @patch('cloner.ticket.Ticket._verify_project')
    def test_get_remote_links_with_no_links(self, mock_verify, mock_session):
        """Test that remote links property is None if there are none."""
        mock_verify.return_value = True
        mock_session.return_value = FakeSession(remote_links=True,
                                                status_code=404)
        t = Ticket()
        self.assertIsNone(t.remote_links)


class TestCallsToSession(unittest.TestCase):
    """Tests for methods that do calls to ticket.s but don't care about
    response.

    These need to be separated because they mock requests.Session differently.
    """

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.patcher = patch('cloner.ticket.Ticket._create_requests_session')
        self.mock_session = self.patcher.start()
        self.mock_session.return_value = MagicMock(speck=requests.Session)
        self.t = Ticket()
        # need to reset get() because it was called during Ticket.__init__
        self.t.s.get.reset_mock()

    def test_add_pav(self):
        """Test that method calls right method."""
        self.t.add_pav("spam-1.0")
        self.t.s.put.assert_called_with(
            '{}/{}'.format(self.t.rest_url, self.t.ticket_id),
            json={'update': {'customfield_11911':
                            [{'add': {'value': 'spam-1.0'}}]}})

    def test_change_subtask_position_with_subtask_ticket(self):
        """Test that subtask positions are not changed if called with subtask.
        """
        self.t.content = {'fields': {'issuetype': {'name': 'Sub-task'}}}
        self.t.change_subtask_position(1)
        self.t.s.get.assert_not_called()

    def test_change_subtask_position_with_no_subtasks(self):
        """Test that subtask positions are not changed if has no subtasks.
        """
        self.t.content = {'fields': {'issuetype': {'name': 'Task'},
                                     'subtasks': []}}
        self.t.change_subtask_position(1)
        self.t.s.get.assert_not_called()

    def test_change_subtask_position_with_position_less_than_zero(self):
        """Test that subtask positions are not changed if called with position
        less than zero.
        """
        self.t.content = {'fields': {'issuetype': {'name': 'Task'},
                                     'subtasks': [1, 2]}}
        self.t.change_subtask_position(-1)
        self.t.s.get.assert_not_called()

    def test_change_subtask_position_with_position_more_than_nr_of_subtasks(
            self):
        """Test that subtask positions are not changed if called with position
        more than number of subtasks.
        """
        self.t.content = {'fields': {'issuetype': {'name': 'Task'},
                                     'subtasks': [1, 2]}}
        self.t.change_subtask_position(3)
        self.t.s.get.assert_not_called()

    def test_change_subtask_position(self):
        """Test that subtask positions are changed."""
        self.t.content = {'fields': {'issuetype': {'name': 'Task'},
                                     'subtasks': [1, 2, 3, 4]},
                          'id': '12345'}
        self.t.change_subtask_position(1)
        self.t.s.get.assert_called_with(
            'https://projects.stage.engineering.redhat.com/secure/MoveIssueLink.jspa?id=12345&currentSubTaskSequence=3&subTaskSequence=1')  # noqa

    def test_verify_subtask_position_valid(self):
        """Test that valid position returns None and raw_input is not called
        when subtask position is valid.
        """
        self.t.content = {'fields': {'issuetype': {'name': 'Task'},
                                     'subtasks': [1, 2]}}
        with patch('__builtin__.raw_input') as _raw_input:
            self.assertIsNone(self.t.verify_position(1))
            _raw_input.assert_not_called()

    def test_verify_subtask_position_invalid_with_user_input_y(self):
        """Test that invalid positioni with user input 'y' returns None
        and raw_input was called
        """
        self.t.content = {'fields': {'issuetype': {'name': 'Task'},
                                     'subtasks': [1, 2]}}
        with patch('__builtin__.raw_input', return_value='y') as _raw_input:
            self.assertIsNone(self.t.verify_position(-1))
            _raw_input.assert_called()

    def test_verify_subtask_position_invalid_with_user_input_n(self):
        """Test that invalid positioni with user input 'n' returns SystemExit
        and raw_input was called
        """
        self.t.content = {'fields': {'issuetype': {'name': 'Task'},
                                     'subtasks': [1, 2]}}
        with patch('__builtin__.raw_input', return_value='n') as _raw_input:
            with self.assertRaises(SystemExit):
                self.t.verify_position(-1)
            _raw_input.assert_called()

if __name__ == '__main__':
    unittest.main()
