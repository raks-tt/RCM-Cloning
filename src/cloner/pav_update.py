#!/usr/bin/env python2

import argparse
import logging
import sys

from ticket import Ticket
from utils import get_ticket_IDs


def main():
    log = logging.getLogger()
    parser = create_parser()
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_usage()
        sys.exit(1)
    if args.debug:
        log.setLevel(logging.DEBUG)
    prod = args.server == 'prod'
    if not args.pav or not args.pav_append:
        parser.error('Arguments PAV and PAVAppend are required')
    append_pav_to_tickets(args.pav, args.pav_append, prod=prod,
                          dry_run=args.dry_run)


def create_parser():
    """Create parser with all required arguments.

    Returns:
        argparse.ArgumentParser object with all args
    """
    parser = argparse.ArgumentParser(
        description="Tool to append PAVs to RCM templates in JIRA ")
    parser.add_argument("--version", action="version", version="1.0")
    parser.add_argument("--server", default="stage",
                        choices=("stage", "prod"),
                        help="JIRA server to use, default stage")
    parser.add_argument("--pav",
                        help="Find all tickets with this PAV and append "
                             "new PAV to them.")
    parser.add_argument("--pav-append",
                        help="PAV value that will be appended to all "
                             "tickets.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Do not perform actions, just provide output "
                             "about what would happen.")
    parser.add_argument("--debug", action="store_true",
                        help="Print debug messages. It's very spammy.")
    return parser


def append_pav_to_tickets(pav, pav_append, prod=False, dry_run=False):
    """Find tickets with given PAV and append new PAV to them.

    Args:
        pav: Existing PAV to search with
        pav_append: New PAV that will be added to tickets
        prod: Choose if production JIRA is used, default False
        dry_run: If True action is not performed, just logged, default False
    """
    ticket_ids = get_ticket_IDs(prod=prod, pav=pav)
    if not ticket_ids:
        logging.error('No tickets match provided PAV')
        return
    for ticket_id in ticket_ids:
        logging.debug('Appending PAV to ticket {0}'.format(ticket_id))
        if not dry_run:
            ticket = Ticket(prod=prod, ticket_id=ticket_id)
            ticket.add_pav(pav_append)


if __name__ == '__main__':
    main()
