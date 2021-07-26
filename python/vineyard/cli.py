#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2020-2021 Alibaba Group Holding Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""vineyard-ctl: A command line tool for vineyard."""

from argparse import ArgumentParser
import sys
import os
import json
import pandas as pd

import vineyard


def vineyard_argument_parser():
    """Utility to create a command line Argument Parser."""
    parser = ArgumentParser(prog='vineyard-ctl',
                            usage='%(prog)s [options]',
                            description='vineyard-ctl: A command line tool for vineyard',
                            allow_abbrev=False)
    parser.add_argument('--version', action='version', version=f'{parser.prog} v{vineyard.__version__}')
    parser.add_argument('--ipc_socket', help='Socket location of connected vineyard server')
    parser.add_argument('--rpc_host', help='RPC HOST of the connected vineyard server')
    parser.add_argument('--rpc_port', type=int, help='RPC PORT of the connected vineyard server')
    parser.add_argument('--rpc_endpoint', help='RPC endpoint of the connected vineyard server')

    cmd_parser = parser.add_subparsers(title='commands', dest='cmd')

    ls_opt = cmd_parser.add_parser('ls', help='List vineyard objects')
    ls_opt.add_argument('--pattern',
                        default='*',
                        type=str,
                        help='The pattern string that will be matched against the object’s typename')
    ls_opt.add_argument('--regex',
                        action='store_true',
                        help='The pattern string will be considered as a regex expression')
    ls_opt.add_argument('--limit', default=5, type=int, help='The limit to list')

    query_opt = cmd_parser.add_parser('query', help='Get a vineyard object')
    query_opt.add_argument('--object_id', required=True, help='ID of the object to be fetched')
    query_opt.add_argument('--meta', choices=['simple', 'json'], help='Metadata of the object')
    query_opt.add_argument('--metric', choices=['nbytes', 'signature', 'typename'], help='Metric data of the object')
    query_opt.add_argument('--exists', action='store_true', help='Check if the object exists or not')
    query_opt.add_argument('--copy', action='store_true', help='Copy the object')
    query_opt.add_argument('--head', action='store_true', help='Get the head of the object')
    query_opt.add_argument('--stdout', action='store_true', help='Get object to stdout')
    query_opt.add_argument('--output_file', type=str, help='Get object to file')
    query_opt.add_argument('--tree', action='store_true', help='Get object lineage in tree-like style')

    del_opt = cmd_parser.add_parser('del', help='Delete a vineyard object')
    del_opt.add_argument('--object_id', required=True, help='ID of the object to be deleted')
    del_opt.add_argument('--force',
                         action='store_true',
                         help='Recursively delete even if the member object is also referred by others')
    del_opt.add_argument('--deep',
                         action='store_true',
                         help='Deeply delete an object means we will deleting the members recursively')

    stat_opt = cmd_parser.add_parser('stat', help='Get the status of connected vineyard server')
    stat_opt.add_argument('--instance_id',
                          dest='properties',
                          action='append_const',
                          const='instance_id',
                          help='Instance ID of vineyardd that the client is connected to')
    stat_opt.add_argument('--deployment',
                          dest='properties',
                          action='append_const',
                          const='deployment',
                          help='The deployment mode of the connected vineyardd cluster')
    stat_opt.add_argument('--memory_usage',
                          dest='properties',
                          action='append_const',
                          const='memory_usage',
                          help='Memory usage (in bytes) of current vineyardd instance')
    stat_opt.add_argument('--memory_limit',
                          dest='properties',
                          action='append_const',
                          const='memory_limit',
                          help='Memory limit (in bytes) of current vineyardd instance')
    stat_opt.add_argument('--deferred_requests',
                          dest='properties',
                          action='append_const',
                          const='deferred_requests',
                          help='Number of waiting requests of current vineyardd instance')
    stat_opt.add_argument('--ipc_connections',
                          dest='properties',
                          action='append_const',
                          const='ipc_connections',
                          help='Number of alive IPC connections on the current vineyardd instance')
    stat_opt.add_argument('--rpc_connections',
                          dest='properties',
                          action='append_const',
                          const='rpc_connections',
                          help='Number of alive RPC connections on the current vineyardd instance')

    put_opt = cmd_parser.add_parser('put', help='Put python value to vineyard')

    put_opt_group = put_opt.add_mutually_exclusive_group(required=True)
    put_opt_group.add_argument('--value', help='The python value you want to put to the vineyard server')
    put_opt_group.add_argument('--file', help='The file you want to put to the vineyard server as a pandas dataframe')

    config_opt = cmd_parser.add_parser('config', help='Edit configuration file')
    config_opt.add_argument('--ipc_socket_value', help='The ipc_socket value to enter in the config file')
    config_opt.add_argument('--rpc_host_value', help='The rpc_host value to enter in the config file')
    config_opt.add_argument('--rpc_port_value', help='The rpc_port value to enter in the config file')
    config_opt.add_argument('--rpc_endpoint_value', help='The rpc_endpoint value to enter in the config file')

    return parser


optparser = vineyard_argument_parser()


def exit_with_help():
    """Utility to exit the program with help message in case of any error."""
    optparser.print_help(sys.stderr)
    sys.exit(-1)


def connect_vineyard(args):
    """Utility to create a vineyard client using an IPC or RPC socket."""
    if args.ipc_socket is not None:
        client = vineyard.connect(args.ipc_socket)
        # force use rpc client in cli tools
        client = vineyard.connect(*client.rpc_endpoint.split(':'))
    elif args.rpc_endpoint is not None:
        client = vineyard.connect(*args.rpc_endpoint.split(':'))
    elif args.rpc_host is not None and args.rpc_port is not None:
        client = vineyard.connect(args.rpc_host, args.rpc_port)
    else:
        client = connect_via_config_file()

    return client


def connect_via_config_file():
    """Utility to create a vineyard client using an IPC or RPC socket from config file."""
    try:
        with open(os.path.expanduser('~/.vineyard/config')) as config_file:
            sockets = config_file.readlines()
        ipc_socket = sockets[0].split(':')[1][:-1]
        rpc_host = sockets[1].split(':')[1][:-1]
        try:
            rpc_port = int(sockets[2].split(':')[1][:-1])
        except:
            rpc_port = None
        rpc_endpoint = sockets[3].split(':')[1][:-1]
    except BaseException as exc:
        raise Exception(f'The config file is either not present or not formatted correctly.\n{exc}') from exc
    if ipc_socket:
        client = vineyard.connect(ipc_socket)
        # force use rpc client in cli tools
        client = vineyard.connect(*client.rpc_endpoint.split(':'))
    elif rpc_endpoint:
        client = vineyard.connect(*rpc_endpoint.split(':'))
    elif rpc_host and rpc_port:
        client = vineyard.connect(rpc_host, rpc_port)
    else:
        exit_with_help()

    return client


def as_object_id(object_id):
    """Utility to convert object_id to an integer if possible else convert to a vineyard.ObjectID."""
    try:
        return int(object_id)
    except ValueError:
        return vineyard.ObjectID.wrap(object_id)


def list_obj(client, args):
    """Utility to list vineyard objects."""
    try:
        objects = client.list_objects(pattern=args.pattern, regex=args.regex, limit=args.limit)
        print(f"List of your vineyard objects:\n{objects}")
    except BaseException as exc:
        raise Exception(f'The following error was encountered while listing vineyard objects:\n{exc}') from exc


def query(client, args):
    """Utility to fetch a vineyard object based on object_id."""
    try:
        value = client.get_object(as_object_id(args.object_id))
        print(f"The vineyard object you requested:\n{value}")
    except BaseException as exc:
        if args.exists:
            print(f"The object with object_id({args.object_id}) doesn't exists")
        raise Exception(('The following error was encountered while fetching ' +
                         f'the vineyard object({args.object_id}):\n{exc}')) from exc

    if args.exists:
        print(f'The object with object_id({args.object_id}) exists')
    if args.stdout:
        sys.stdout.write(str(value) + '\n')
    if args.output_file is not None:
        with open(args.output_file, 'w') as output_file:
            output_file.write(str(value))
    if args.meta is not None:
        if args.meta == 'simple':
            print(f'Meta data of the object:\n{value.meta}')
        elif args.meta == 'json':
            json_meta = json.dumps(value.meta, indent=4)
            print(f'Meta data of the object in JSON format:\n{json_meta}')
    if args.metric is not None:
        print(f'{args.metric}: {getattr(value, args.metric)}')


def delete_obj(client, args):
    """Utility to delete a vineyard object based on object_id."""
    try:
        client.delete(object_id=as_object_id(args.object_id), force=args.force, deep=args.deep)
        print(f'The vineyard object({args.object_id}) was deleted successfully')
    except BaseException as exc:
        raise Exception(('The following error was encountered while deleting ' +
                         f'the vineyard object({args.object_id}):\n{exc}')) from exc


def status(client, args):
    """Utility to print the status of connected vineyard server."""
    stat = client.status
    if args.properties is None:
        print(stat)
    else:
        print('InstanceStatus:')
        for prop in args.properties:
            print(f'    {prop}: {getattr(stat, prop)}')


def put_object(client, args):
    """Utility to put python value to vineyard server."""
    if args.value is not None:
        try:
            value = args.value
            client.put(value)
            print(f'{value} was successfully put to vineyard server')
        except BaseException as exc:
            raise Exception(('The following error was encountered while putting ' +
                             f'{args.value} to vineyard server:\n{exc}')) from exc
    elif args.file is not None:
        try:
            value = pd.read_csv(args.file)
            client.put(value)
            print(f'{value} was successfully put to vineyard server')
        except BaseException as exc:
            raise Exception(('The following error was encountered while putting ' +
                             f'{args.file} as pandas dataframe to vineyard server:\n{exc}')) from exc


def config(args):
    """Utility to edit the config file."""
    with open(os.path.expanduser('~/.vineyard/config')) as config_file:
        sockets = config_file.readlines()
    with open(os.path.expanduser('~/.vineyard/config'), 'w') as config_file:
        if args.ipc_socket_value is not None:
            sockets[0] = f'ipc_socket:{args.ipc_socket_value}\n'
        if args.rpc_host_value is not None:
            sockets[1] = f'rpc_host:{args.rpc_host_value}\n'
        if args.rpc_port_value is not None:
            sockets[2] = f'rpc_port:{args.rpc_port_value}\n'
        if args.rpc_endpoint_value is not None:
            sockets[3] = f'rpc_endpoint:{args.rpc_endpoint_value}'
        config_file.writelines(sockets)


def main():
    """Main function for vineyard-ctl."""
    args = optparser.parse_args()
    if args.cmd is None:
        return exit_with_help()

    if args.cmd == 'config':
        return config(args)

    client = connect_vineyard(args)

    if args.cmd == 'ls':
        return list_obj(client, args)
    if args.cmd == 'query':
        return query(client, args)
    if args.cmd == 'del':
        return delete_obj(client, args)
    if args.cmd == 'stat':
        return status(client, args)
    if args.cmd == 'put':
        return put_object(client, args)

    return exit_with_help()


if __name__ == "__main__":
    main()
