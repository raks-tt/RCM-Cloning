import logging

from ticket import Ticket


class Cloner():
    """Class that performs all the cloning related work.

    Args:
        tickets: List of Ticket objects
        project: String project key in JIRA in which new ticket is created
        inject: Dictionary with values for injecting formatted for JIRA API,
                default None
        custom_substitutions: Dict with {VAR:value} used for pattern
                                  replacement. Default is None
        only_matched: Bool value to choose if only tickets that match some
                      previously ran query should be cloned; these tickets
                      are expected in self.tickets, if ticket is of type
                      'Sub-task' and its parent doesn't match they will not
                      be cloned, default False
        prod: Bool value to choose if production JIRA is used, default False
        dry_run: If True action is not performed, just logged, default False
                                  replacement
    """

    def __init__(self, tickets, project, inject=None,
                 custom_substitutions=None, only_matched=False, prod=False,
                 dry_run=False):
        self.tickets = tickets
        self.project = project
        self.inject = inject
        self.custom_substitutions = custom_substitutions
        self.only_matched = only_matched
        self.prod = prod
        self.dry_run = dry_run
        self.log = logging.getLogger()
        if self.only_matched:
            self._ticket_ids = [ticket.ticket_id for ticket in self.tickets]
        self._cloned = {}
        self._links = []
        self._linked = []

    def clone_tickets(self):
        """Clone tickets in self.tickets."""
        for ticket in self.tickets:
            self.clone_ticket(ticket, only_matched=self.only_matched)

    def clone_ticket(self, ticket, parent=None, only_matched=False):
        """Clone one ticket with its parents, subtasks and links.

        Args:
            ticket: Ticket object to clone
            parent: Parent's id in case we know parent ticket, default None
            only_matched: Bool value to choose if only tickets that matched
                          previous query (i.e. tickets in self.tickets) should
                          be cloned, default False
        """
        if ticket.ticket_id in self._cloned:
            return
        if only_matched and ticket.ticket_id not in self._ticket_ids:
            # cloning only matched tickets and this doesn't match
            return
        if ticket.status == 'Deprecated':
            self.log.info('Skipped {0} as it is in deprecated state.'.format(
                ticket.ticket_id))
            return
        if ticket.parent_id and ticket.parent_id not in self._cloned:
            # if it's subtask we first need to create its parent and then
            # subtasks are added when cloning parent task to preserve order
            self.clone_ticket(
                Ticket(
                    prod=self.prod,
                    project=self.project,
                    ticket_id=ticket.parent_id,
                    custom_substitutions=self.custom_substitutions
                ),
                only_matched=only_matched
            )
            return
        new = Ticket(
            prod=self.prod,
            project=self.project,
            custom_substitutions=self.custom_substitutions
            )
        if ticket.issuetype == 'Sub-task':
            self.log.info('Cloning SubTask {0} - {1}'.format(ticket.ticket_id,
                                                             ticket.summary))
        else:
            self.log.info('Cloning Parent {0} - {1}'.format(ticket.ticket_id,
                                                            ticket.summary))
        if not self.dry_run:
            new.clone(ticket, inject=self.inject, parent=parent,
                      custom_substitutions=self.custom_substitutions)
            new.add_comment('This issue was cloned from {0}'.format(
                ticket.ticket_id))
        else:
            # we need generic ticket_id for dry-run
            new.ticket_id = 'ID'
        self._cloned[ticket.ticket_id] = new.ticket_id
        if ticket.subtask_ids:
            for subtask_id in ticket.subtask_ids:
                if subtask_id not in self._cloned:
                    self.clone_ticket(
                        Ticket(
                            prod=self.prod,
                            project=self.project,
                            ticket_id=subtask_id,
                            custom_substitutions=self.custom_substitutions
                        ),
                        parent=new.ticket_id,
                        only_matched=only_matched)
        if ticket.links:
            for link in ticket.links:
                linked_ticket_id, link_type, direction = link
                if linked_ticket_id not in self._cloned:
                    self.clone_ticket(
                        Ticket(
                            prod=self.prod,
                            project=self.project,
                            ticket_id=linked_ticket_id,
                            custom_substitutions=self.custom_substitutions
                        ),
                        only_matched=only_matched)
                self._links.append((ticket.ticket_id, linked_ticket_id,
                                    link_type, direction))

    def clone_subtask_to_existing_parent(self, ticket, parent_id,
                                         position=None):
        """Clone single subtask to already existing parent.

        Args:
            ticket: Ticket object
            parent_id: JIRA id of an existing task
            position: Position of a subtask to be moved to as int, default None
        """
        if ticket.status == 'Deprecated':
            self.log.info('Skipped {0} as it is in deprecated state.'.format(
                ticket.ticket_id))
            return
        parent = Ticket(prod=self.prod, project=self.project,
                        ticket_id=parent_id)
        parent.verify_position(position)
        self.log.info('Cloning SubTask {0} - {1}'.format(ticket.ticket_id,
                                                         ticket.summary))
        new = Ticket(prod=self.prod, project=self.project,
                     custom_substitutions=self.custom_substitutions)
        if not self.dry_run:
            new.clone(ticket, inject=self.inject,
                      custom_substitutions=self.custom_substitutions,
                      parent=parent_id)
        else:
            # we need generic ticket_id for dry-run
            new.ticket_id = 'ID'
        self._cloned[ticket.ticket_id] = new.ticket_id
        if not self.dry_run:
            parent.content = parent._get_content()
            parent.change_subtask_position(position)

    def link_tickets(self):
        """Create links between tickets in self._links."""
        if self.dry_run:
            return
        for link in self._links:
            ticket_id_1, ticket_id_2, link_type, direction = link
            clone_id_1 = self._cloned.get(ticket_id_1)
            clone_id_2 = self._cloned.get(ticket_id_2)
            if not clone_id_1 or not clone_id_2:
                continue
            if ([clone_id_2, clone_id_1] in self._linked or
                    [clone_id_1, clone_id_2] in self._linked):
                continue
            self.log.debug('Linking {0} to {1}'.format(clone_id_1, clone_id_2))
            t = Ticket(prod=self.prod, project=self.project,
                       ticket_id=clone_id_1)
            t.create_link((clone_id_2, link_type, direction))
            self._linked.append([clone_id_1, clone_id_2])
