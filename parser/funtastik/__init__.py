# -*- coding: utf-8 -*-
import logging
import argparse
import sys

from config import LOG_PATH
from parsers import VKParser
from actions import AddAction, RefreshAction, ListAction, RMAction, \
    DoesNotExists, EmptyValueException, AlreadyExist

#logger = logging.getLogger()

#logging.FileHandler(LOG_PATH)
# handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - '
#                                        '%(levelname)s - %(message)s'))
# logger.addHandler(handler)

#logging.info('it works')


class FuntastikParser(object):

    def fun(self):
        try:
            action = self._select_command()
        except EmptyValueException:
            sys.stdout.write("Parameter missed\n")
        except AlreadyExist:
            sys.stdout.write("Item already exists\n")
        except DoesNotExists:
            sys.stdout.write("Item doesn\'t exists")
        else:
            if action is None:
                sys.stdout.write('Unknown command\n')
            sys.stdout.write(str(action) + '\n')

    @staticmethod
    def _parse_args():
        argparser = argparse.ArgumentParser()
        argparser.add_argument('action')
        argparser.add_argument('param', nargs='?')
        return argparser.parse_args()

    def _select_command(self):
        args = self._parse_args()
        action = args.action.lower()
        if action == 'add':
            act = AddAction()
            return act.run(args.param)
        elif action == 'list':
            act = ListAction()
            return act.run()
        elif action == 'refresh':
            act = RefreshAction()
            return act.run()
        elif action == 'rm':
            act = RMAction()
            return act.run(args.param)


