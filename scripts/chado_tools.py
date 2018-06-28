#!/usr/bin/env python3

import sys
import pkg_resources

availableCommands = {
    'create'        : 'create a new instance of the CHADO schema',
    'connect'       : 'connect to a CHADO database',
    'dump'          : 'dump a PostgreSQL instance of the database',
    '-h, --help'    : 'show this help message and exit',
    '-v, --version' : 'show the version of the software'
}


def print_usage_and_exit():
    """Prints an info message to the user describing how to run the program"""
    print('\nusage: chado-tools <command> [options]\n', file=sys.stderr)
    print('Available commands:\n', file=sys.stderr)
    maxStringLength = max([len(cmd) for cmd in list(availableCommands.keys())])
    for command, description in availableCommands.items():
        print('{{0: <{}}}'.format(maxStringLength).format(command), description, sep=' : ', file=sys.stderr)
    print()
    sys.exit(1)


def main():
    """Main routine of the chado-tools package"""
    if len(sys.argv) == 1 or sys.argv[1] in ['-h', '--help']:
        # Display info message
        print_usage_and_exit()
    elif sys.argv[1] in ['-v', '--version']:
        # Display program version
        print(pkg_resources.get_distribution("pychado").version)
    else:
        # Call function depending on entered command
        command = sys.argv[1]
        if command in availableCommands:
            exec('import pychado.runners.' + command)
            exec('pychado.runners.' + command + '.run("' + availableCommands[command] + '")')
        else:
            print('\nUnrecognized option/command "' + command + '".', file=sys.stderr)
            print_usage_and_exit()