import logging
import unittest

from mock import MagicMock, patch, call

from cloner.cloner import Cloner
from cloner.ticket import Ticket


class TestCloner(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)

    @patch('cloner.cloner.Cloner.clone_ticket')
    def test_clone_tickets(self, mock_clone):
        """Test that clone_tickets() calls clone_ticket for all tickets."""
        t1 = MagicMock(spec=Ticket)
        t2 = MagicMock(spec=Ticket)
        t3 = MagicMock(spec=Ticket)
        cloner = Cloner([t1, t2, t3], None)
        cloner.clone_tickets()
        calls = [call(t1, only_matched=False),
                 call(t2, only_matched=False),
                 call(t3, only_matched=False)]
        mock_clone.assert_has_calls(calls)

    @patch('cloner.cloner.Ticket', autospec=True)
    def test_clone_deprecated_ticket(self, mock_ticket):
        """Test that deprecated tickets are not cloned."""
        t = mock_ticket()
        t.ticket_id = 'ID'
        t.status = 'Deprecated'
        cloner = Cloner([], None)
        cloner.clone_ticket(t)
        self.assertEqual(cloner._cloned, {})

    def test_clone_subtask_to_existing_parent_deprecated(self):
        """Test that deprecated subtask isn't cloned."""
        t = MagicMock(spec=Ticket)
        t.ticket_id = 'ID'
        t.status = 'Deprecated'
        cloner = Cloner([], None)
        cloner.clone_subtask_to_existing_parent(t, 'parent')
        self.assertEqual(cloner._cloned, {})

    @patch('cloner.cloner.Ticket', autospec=True)
    def test_link_tickets(self, mock_ticket):
        """Test that tickets are linked and same links are not created multiple
        times.
        """
        cloner = Cloner([], None)
        cloner._links = [('ID-1', 'ID-2', 'type', 'inward'),
                         ('ID-2', 'ID-1', 'type', 'outward')]
        cloner._cloned = {'ID-1': 'CID-1', 'ID-2': 'CID-2'}
        cloner.link_tickets()
        calls = [call(('CID-2', 'type', 'inward'))]
        mock_ticket.return_value.create_link.assert_has_calls(calls)
        self.assertEqual(cloner._linked, [['CID-1', 'CID-2']])


if __name__ == '__main__':
    unittest.main()
