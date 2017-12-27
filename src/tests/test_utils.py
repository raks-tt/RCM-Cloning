import unittest
from mock import patch, MagicMock

from cloner.utils import prepare_inject, get_ticket_IDs, \
    get_ticket_IDs_specific


class TestUtils(unittest.TestCase):

    def test_prepare_inject(self):
        """Test that fields are prepared to be injected."""
        input = {
            "PAV": "spam-1.0",
            "keywords": ["bicycle", "repair", "man"],
            "labels": ["Red Leicester", "Tilsit", "Emmental"],
            "assignee": "Mr. Creosote",
            "milestone": "nudge"
        }
        expected = {
            "customfield_11911": [{"value": "spam-1.0"}],
            "customfield_12700": [
                {"value": "bicycle"},
                {"value": "repair"},
                {"value": "man"}
            ],
            "labels": ["Red Leicester", "Tilsit", "Emmental"],
            "assignee": {"name": "Mr. Creosote"},
            "customfield_12000": [{"value": "nudge"}]
        }
        output = prepare_inject(input)
        self.assertEqual(expected, output)

    @patch('cloner.ticket.Ticket.search')
    @patch('cloner.ticket.Ticket._create_requests_session')
    def test_get_ticket_IDs_query_formatting(self, mock_session, mock_search):
        """Test that get_ticket_IDs_specific() properly formats query before
        search.
        """
        mock_session.return_value = MagicMock()
        get_ticket_IDs_specific('spam-1.0')
        mock_search.assert_called_with('project=RCMTEMPL and '
                                       '"Product Affects Version"="spam-1.0"')
        get_ticket_IDs_specific('spam-1.0', keywords=['spam', 'eggs'])
        mock_search.assert_called_with(
            'project=RCMTEMPL and "Product Affects Version"="spam-1.0" and '
            '((issuetype="Sub-task") or (issuetype!="Sub-task" and '
            '"Keyword"="spam" and "Keyword"="eggs"))')

    @patch('cloner.ticket.Ticket.search')
    @patch('cloner.ticket.Ticket._create_requests_session')
    def test_get_tickets_query_formatting(self, mock_session, mock_search):
        """Test that get_ticket_IDs() properly formats query before search."""
        mock_session.return_value = MagicMock()
        get_ticket_IDs(None)
        mock_search.assert_called_with('project=RCMTEMPL')
        get_ticket_IDs(None, pav='spam-1.0')
        mock_search.assert_called_with('project=RCMTEMPL and '
                                       '"Product Affects Version"="spam-1.0"')
        get_ticket_IDs(None, keywords=['spam', 'eggs'])
        mock_search.assert_called_with('project=RCMTEMPL '
                                       'and "Keyword"="spam" '
                                       'and "Keyword"="eggs"')
        get_ticket_IDs(None, pav='spam-1.0',
                       keywords=['spam', 'eggs'])
        mock_search.assert_called_with('project=RCMTEMPL and '
                                       '"Product Affects Version"="spam-1.0"'
                                       ' and "Keyword"="spam"'
                                       ' and "Keyword"="eggs"')


if __name__ == '__main__':
    unittest.main()
