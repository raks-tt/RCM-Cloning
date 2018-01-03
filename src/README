# RCM templates cloning and manipulation

## Template cloning

Python library and CLI tool for cloning RCM templates in JIRA.

Tool is able to clone only from `RCMTEMPL` JIRA project and doesn't work with tickets with status `Deprecated`.

To run the tool use `cloner/jira_clone_template_rcm.py` with appropriate arguments:
```
$ ./jira_clone_template_rcm.py [-h] [--version] [--server {stage,prod}]
                               [--project {RCM,RCMWORK}] [--pav PAV]
                               [--component COMPONENT] [--label LABEL]
                               [--milestone MILESTONE]
                               [--assignee ASSIGNEE] [--reporter REPORTER]
                               [--custom-text CUSTOM_TEXT]
                               [--position POSITION]
                               [--type {clone,search}] [--subtask SUBTASK]
                               [--parent PARENT] [--dry-run]
                               [--verbose]
```

## Template modifying

Python library and CLI tool for RCM templates manipulation.

Tool is currently able to append value to PAV field to templates in `RCMTEMPL` JIRA project.

To run the tool use `cloner/pav_update.py` with appropriate arguments:
```
$ ./pav_update.py [-h] [--version] [--server {stage,prod}] [--pav PAV]
                  [--pav-append PAVAPPEND] [--dry-run] [--debug]
```

# Dependencies

This library requires python [ticketutil](https://pypi.python.org/pypi/ticketutil/1.2.0) library which is available through pip:
```
$ pip install ticketutil
```

# Testing

Code comes with a set of unittests. To run them call:
```
$ python -m unittest discover tests
```
