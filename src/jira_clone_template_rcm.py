#!/usr/bin/env python2

import argparse
import logging
import sys

from ticket import Ticket
from cloner import Cloner
from utils import prepare_inject, get_ticket_IDs, get_ticket_IDs_specific


def main():
    log = logging.getLogger()
    parser = create_parser()
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_usage()
        sys.exit(1)

    if args.debug:
        log.setLevel(logging.DEBUG)

    fields = extract_fields(args)
    prod = args.server == 'prod'
    # Be ready for more incoming substitutions if needed
    custom_substitutions = {}
    if args.custom_text:
        custom_substitutions['CUSTOM_TEXT'] = args.custom_text
    log.debug("custom_substitutions={0}".format(custom_substitutions))
    if args.type == 'search':
        search_tickets(log, fields.get('PAV'), fields.get('keywords'),
                       prod=prod)
    elif args.type == 'clone':
        if not args.parent and args.pav:
            inject = prepare_inject(fields, prod=prod)
            search_and_clone_specific_tickets(
                args.pav, fields.get('keywords'), args.project, inject,
                prod=prod,
                dry_run=args.dry_run,
                custom_substitutions=custom_substitutions)
        elif args.subtask and args.parent:
            inject = prepare_inject(fields, prod=prod)
            adjusted_position = (int(args.position) - 1
                                 if args.position
                                 else None)
            clone_subtask_to_existing_parent(
                args.subtask.upper(),
                args.parent.upper(),
                args.project, inject,
                position=adjusted_position,
                prod=prod,
                dry_run=args.dry_run,
                custom_substitutions=custom_substitutions)
        elif args.parent:
            inject = prepare_inject(fields, prod=prod)
            ticket_ids = [ticket_id.strip().upper()
                          for ticket_id in args.parent.split(',')]
            clone_tickets(ticket_ids, args.project, inject,
                          prod=prod, dry_run=args.dry_run,
                          custom_substitutions=custom_substitutions)
        else:
            parser.error('Invalid combination of arguments provided, please '
                         'refer to documentation '
                         '(https://mojo.redhat.com/docs/DOC-1147075) for '
                         'usage examples.')


def create_parser():
    """Create parser with all required arguments.

    Returns:
        argparse.ArgumentParser object with all args
    """
    parser = argparse.ArgumentParser(
        description="Tool to clone RCM templates in JIRA "
                    "(https://mojo.redhat.com/docs/DOC-1147075)")
    parser.add_argument("--version", action="version", version="1.1")
    parser.add_argument("--server", default="stage", choices=("stage", "prod"),
                        help="JIRA server to use, default stage")
    parser.add_argument("--project", default="RCM",
                        choices=("RCM", "RCMWORK"),
                        help="JIRA project key in which new tickets are "
                             "created, default RCM")
    parser.add_argument("--pav",
                        help="If used with --parent then overrides Product "
                             "Affects Version field in all new tickets with "
                             "provided PAV, if used without --parent then "
                             "clones tickets that match given PAV; if used "
                             "with --type search, use provided PAV to search "
                             "with")
    parser.add_argument("--keywords",
                        help="If used with --parent then overrides keywords "
                             "field in all new tickets with comma separated "
                             "provided values, if used without --parent then "
                             "requires --pav and clones tickets that match "
                             "given keywords and PAV (keywords matching "
                             "not performed on subtasks); if used with --type "
                             "search, use provided keywords to search with")
    parser.add_argument("--label",
                        help="Override Label field in all new tickets with "
                             "provided comma separated values; has no effect "
                             "with --type search")
    parser.add_argument("--milestone",
                        help="Override Target Milestone field on all new "
                             "tickets with provided value, default is "
                             "currently logged in user;  has no effect with "
                             "--type search")
    parser.add_argument("--assignee",
                        help="Override Assignee field on all new tickets with "
                             "provided value, default is currently logged in "
                             "user; has no effect with --type search")
    parser.add_argument("--reporter",
                        help="Override Reporter field on all new tickets with "
                             "provided value, default is currently logged in "
                             "user; has no effect with --type search")
    parser.add_argument("--position",
                        help="Position into which cloned subtask should be "
                             "moved to; has effect only when used with "
                             "--parent and --subtask")
    parser.add_argument("--type", default="clone", choices=("clone", "search"),
                        help="Action to perform; 'clone' tries to clone "
                             "provided tickets, 'search' prints ticket id, "
                             "summary, pav and labels for tickets that match "
                             "given parameters, default clone")
    parser.add_argument("--subtask",
                        help="JIRA ID of a subtask, that will be cloned into "
                             "existing parent task; requires --parent; has no "
                             "effect with --type search")
    parser.add_argument("--parent",
                        help="Coma separated JIRA ticket IDs to be cloned if "
                             "used without --subtask. If used with --subtask "
                             "it is existing JIRA task ID (has to be in the "
                             "same project as --project), which will be a "
                             "parent of a cloned subtask; has no effect with "
                             "--type search")
    parser.add_argument("--dry-run", action="store_true",
                        help="Do not perform actions, just provide output "
                             "about what would happen.")
    parser.add_argument("--debug", action="store_true",
                        help="Print debug messages. It's very spammy.")
    parser.add_argument("--custom-text",
                        help="Substitute <CUSTOM_TEXT> in JIRA with a value")
    return parser


def extract_fields(args):
    """Create dictionary from fields that were passed to command line.

    Args:
        args: argparse.Namespace instance

    Returns:
        Dictionary with passed arguments as keys and their respective values
    """
    fields = {}
    if args.pav:
        fields["PAV"] = args.pav
    if args.label:
        fields['labels'] = [label.strip() for label in args.label.split(',')]
    if args.keywords:
        fields['keywords'] = [keyword.strip() for keyword
                              in args.keywords.split(',')]
    if args.milestone:
        fields['milestone'] = args.milestone
    if args.assignee:
        fields['assignee'] = args.assignee
    if args.reporter:
        fields['reporter'] = args.reporter
    return fields


def search_tickets(log, pav, keywords, prod=False):
    """Perform ticket search in JIRA based on provided values and output
    number of tickets found, their IDs, summaries, PAVs and labels.

    Args:
        log: Logger object
        pav: String Product Affects Version field
        keywords: List of keywords
        prod: Choose if production JIRA is used, default False
    """
    ticket_ids = get_ticket_IDs(pav=pav, keywords=keywords, prod=prod)
    log.info('Nr. of tickets found: {0}'.format(len(ticket_ids)))
    for ticket_id in ticket_ids:
        ticket = Ticket(prod=prod, ticket_id=ticket_id)
        log.info('Ticket: {0} - {1}'.format(ticket.ticket_id, ticket.summary))
        pav = ticket.pav
        labels = ticket.labels
        log.info('PAV: {0}, Labels: {1}'.format(
            ", ".join(pav) if pav else None,
            ", ".join(labels) if labels else None))


def search_and_clone_specific_tickets(pav, keywords, project, inject,
                                      prod=False, dry_run=False,
                                      custom_substitutions=None):
    """Perform cloning of tickets that match specified pav and keywords.

    Keyword matching is not performed for tickets of type Sub-task.

    Args:
        pav: String Product Affects Version field
        keywords: List of keywords
        project: String project key in JIRA in which new tickets are created
        inject: Dictionary with values for injecting formatted for JIRA API
        prod: Choose if production JIRA is used, default False
        dry_run: If True action is not performed, just logged, default False
        custom_substitutions: dict containing VAR: substitution
    """
    ticket_ids = get_ticket_IDs_specific(pav, keywords=keywords, prod=prod)
    tickets = []
    for ticket_id in ticket_ids:
        tickets.append(
            Ticket(
                prod=prod,
                ticket_id=ticket_id,
                custom_substitutions=custom_substitutions
                )
        )
    cloner = Cloner(tickets, project, inject=inject,
                    custom_substitutions=custom_substitutions,
                    only_matched=True,
                    prod=prod, dry_run=dry_run)
    cloner.clone_tickets()
    cloner.link_tickets()


def clone_tickets(ticket_ids, project, inject, prod=False,
                  dry_run=False, custom_substitutions=None):
    """Perform cloning of tickets with all their links, parents and subtasks.

    Args:
        ticket_ids: List of ticket IDs to be cloned
        project: String project key in JIRA in which new tickets are created
        inject: Dictionary with values for injecting formatted for JIRA API
        prod: Choose if production JIRA is used, default False
        dry_run: If True action is not performed, just logged, default False
        custom_substitutions: dict with {"VAR": "substitution",}
    """
    tickets = []
    for id in ticket_ids:
        tickets.append(
            Ticket(
                prod=prod,
                ticket_id=id,
                custom_substitutions=custom_substitutions,
            )
        )
    cloner = Cloner(tickets, project, inject=inject,
                    custom_substitutions=custom_substitutions,
                    prod=prod, dry_run=dry_run)
    cloner.clone_tickets()
    cloner.link_tickets()


def clone_subtask_to_existing_parent(subtask_id, parent_id, project, inject,
                                     position=None,
                                     prod=False, dry_run=False,
                                     custom_substitutions=None):
    """Clone single subtask to existing parent task.

    Args:
        subtask_id: String JIRA id of a subtask
        parent_id: String JIRA id of an existing task
        project: String project key in JIRA in which new tickets are created
        inject: Dictionary with values for injecting formatted for JIRA API
        position: Position of a subtask to be moved to as int, default None
        prod: Choose if production JIRA is used, default False
        dry_run: If True action is not performed, just logged, default False
        custom_substitutions: dict with {"VAR": "substitution",}
    """
    cloner = Cloner(
                [],
                project,
                inject=inject,
                prod=prod,
                dry_run=dry_run,
                custom_substitutions=custom_substitutions,
            )
    cloner.clone_subtask_to_existing_parent(
        Ticket(
            prod=prod,
            ticket_id=subtask_id,
            custom_substitutions=custom_substitutions),
        parent_id,
        position=position
    )
    cloner.link_tickets()


if __name__ == "__main__":
    main()
