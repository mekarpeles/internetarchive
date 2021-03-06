# -*- coding: utf-8 -*-
#
# The internetarchive module is a Python/CLI interface to Archive.org.
#
# Copyright (C) 2012-2019 Internet Archive
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Retrieve information about your catalog tasks.

For more information on how to use this command, refer to the
Tasks API documentation::

    https://archive.org/services/docs/api/tasks.html

usage:
    ia tasks [--task=<task_id>...] [--get-task-log=<task_id>]
             [--parameter=<k:v>...]
    ia tasks <identifier> [--parameter=<k:v>...]
    ia tasks <identifier> --cmd=<command> --comment=<comment>
                          [--data=<k:v>...]
    ia tasks --help

options:
    -h, --help
    -t, --task=<task_id>...       Return information about the given task.
    -G, --get-task-log=<task_id>  Return the given tasks task log.
    -p, --parameter=<k:v>...      URL parameters passed to catalog.php.
    -c, --cmd=<command>           The task to submit (e.g. make_dark.php).
    -C, --comment=<command>       A reasonable explantion for why a
                                  task is being submitted.
    -d, --data=<k:v>...           Additional data to send when submitting
                                  a task.

examples:
    ia tasks nasa
    ia tasks nasa -p cmd:derive.php  # only return derive.php tasks
    ia tasks -p 'args:*s3-put*'  # return all S3 tasks
    ia tasks -p 'submitter=jake@archive.org'  # return all tasks submitted by a user
    ia tasks --get-task-log 1178878475  # get a task log for a specific task

    ia tasks <id> --cmd make_undark.php --comment '<comment>'  # undark item
    ia tasks <id> --cmd make_dark.php --comment '<comment>'  # dark item
"""
from __future__ import absolute_import, print_function
import sys

from docopt import docopt
import six

from internetarchive.cli.argparser import get_args_dict


def main(argv, session):
    args = docopt(__doc__, argv=argv)

    # Tasks write API.
    if args['--cmd']:
        data = get_args_dict(args['--data'], query_string=True)
        r = session.submit_task(args['<identifier>'],
                                args['--cmd'],
                                comment=args['--comment'],
                                priority=data.get('priority'),
                                data=data)
        j = r.json()
        if j.get('success'):
            print('success: {}'.format(j.get('value', dict()).get('log')))
            sys.exit(0)
        else:
            print('error: {}'.format(j.get('error')))
            sys.exit(1)

    # Tasks read API.
    params = get_args_dict(args['--parameter'], query_string=True)
    if args['<identifier>']:
        _params = dict(identifier=args['<identifier>'], catalog=1, history=1)
        _params.update(params)
        params = _params
    elif args['--get-task-log']:
        log = session.get_task_log(args['--get-task-log'], params)
        if six.PY2:
            print(log.encode('utf-8'))
        else:
            print(log)
        sys.exit(0)

    queryable_params = [
        'identifier',
        'task_id',
        'server',
        'cmd',
        'args',
        'submitter',
        'priority',
        'wait_admin',
        'submittime',
    ]

    if not args['<identifier>'] \
            and not params.get('task_id'):
        params.update(dict(catalog=1, history=0))

    if not any(x in params for x in queryable_params):
        _params = dict(submitter='jake@archive.org', catalog=1, history=0, summary=0)
        _params.update(params)
        params = _params

    for t in session.get_tasks(params=params):
        print(t.json())
        sys.stdout.flush()
