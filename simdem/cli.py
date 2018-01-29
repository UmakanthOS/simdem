#!/usr/local/bin/python3
""" Entrypoint to Simdem """
import configparser
import logging
import argparse
import os
import pkg_resources

from simdem.executor import bash
from simdem.parser import ast, simdem1
from simdem.mode import demo, dump, test, tutorial


def main():
    """ Main execution function """
    argp = argparse.ArgumentParser()
    argp.add_argument('file', metavar='file',
                      help='file to process')
    argp.add_argument('--debug', '-d', action="store_true",
                      help="Turn on logging to console")
    argp.add_argument('--config-file', '-c',
                      help="Config file to use")
    argp.add_argument('--mode', '-m', default="tutorial",
                      help="Mode to use", choices=['demo', 'dump', 'test', 'tutorial'])
    argp.add_argument('--parser', '-p', default="simdem1",
                      help="Parser class to use", choices=['simdem1', 'ast'])
    argp.add_argument('--executor', '-e', default="bash",
                      help="Executor class to use", choices=['bash'])
    argp.add_argument('--setting', '-s', metavar='setting',
                      help="Setting to override in config file")
    options = argp.parse_args()

    file_path = options.file
    config_file_path = get_config_file_path(options)
    validate(file_path, config_file_path)

    config = configparser.ConfigParser()
    config.read(config_file_path)
    inject_arguments(options, config)

    setup_logging(config, options)

    mode = get_mode(options, config)
    mode.process_file(file_path)

def get_config_file_path(options):
    """ Returns the found config file path """
    options_config_file = options.config_file
    if options_config_file:
        return options_config_file
    file_path = pkg_resources.resource_filename(__name__, 'simdem.ini')
    return file_path

def inject_arguments(options, config):
    """ Injects CLI arguments into config settings """
    if options.setting:
        [key, value] = options.setting.split('=')
        [section, option] = key.split('.')
        config.set(section, option, value)

def validate(file_path, config_file_path):
    """ validate all passed in arguments """
    if not os.path.isfile(file_path):
        raise FileNotFoundError('Unable to find file: ' + file_path)

    if not os.path.isfile(config_file_path):
        raise FileNotFoundError('Unable to find config file: ' + config_file_path)

def get_mode(options, config):
    """ Returns correct renderer object """

    parser = get_parser(options)
    executor = get_executor(options)

    if options.mode == 'demo':
        return demo.DemoMode(config, parser, executor)

    if options.mode == 'dump':
        return dump.DumpMode(config, parser, executor)

    if options.mode == 'test':
        return test.TestMode(config, parser, executor)

    if options.mode == 'tutorial':
        return tutorial.TutorialMode(config, parser, executor)

def get_parser(options):
    """ Returns correct parser object """
    if options.parser == 'ast':
        return ast.AstParser()
    elif options.parser == 'simdem1':
        return simdem1.SimDem1Parser()

def get_executor(options):
    """ Returns correct executor object """
    if options.executor == 'bash':
        return bash.BashExecutor()

def setup_logging(config, options):
    """ Establishes logging level and format """
    log_formatter = logging.Formatter(config.get('log', 'format', raw=True))
    root_logger = logging.getLogger()
    root_logger.setLevel(config.get('log', 'level'))

    file_handler = logging.FileHandler(config.get('log', 'file'))
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    if options.debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)
