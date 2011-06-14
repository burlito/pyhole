#   Copyright 2010-2011 Josh Kearney
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Pyhole Utility Library"""

from __future__ import with_statement

import eventlet
import logging
import logging.handlers
import os
import re
import sys

import config


eventlet.monkey_patch()


def logger(name, debug=False):
    """Log handler"""
    log_dir = get_home_directory() + "logs"
    level = logging.DEBUG if debug else logging.INFO
    format = "%(asctime)s [%(name)s] %(message)s"
    datefmt = "%H:%M:%S"

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(level=level, format=format, datefmt=datefmt)

    log = logging.handlers.TimedRotatingFileHandler("%s/%s.log" % (log_dir,
            name.lower()), "midnight")
    log.setLevel(level)
    formatter = logging.Formatter(format, datefmt)
    log.setFormatter(formatter)
    logging.getLogger(name).addHandler(log)

    return logging.getLogger(name)


def admin(func):
    """Administration Decorator"""
    def f(self, *args, **kwargs):
        if self.irc.source in self.irc.admins:
            func(self, *args, **kwargs)
        else:
            self.irc.reply("Sorry, you are not authorized to do that.")
    f.__doc__ = func.__doc__
    f.__name__ = func.__name__
    f.__module__ = func.__module__
    return f


def spawn(func):
    """Greenthread Spawning Decorator"""
    def f(self, *args, **kwargs):
        eventlet.spawn_n(func, self, *args, **kwargs)
    f.__doc__ = func.__doc__
    f.__name__ = func.__name__
    f.__module__ = func.__module__
    return f


def decode_entities(html):
    """Strip HTML entities from a string"""
    entities = [
        ("<[^>]*?>", ""),
        ("&nbsp;", " "),
        ("&amp;", "&"),
        ("&quot;", "\""),
        ("&#8212;", "-"),
        ("&#8217;", "'"),
        ("&#39;", "'"),
        ("&#8220;", "\""),
        ("&#8221;", "\""),
        ("&#8230;", "..."),
        ("&#x22;", "\""),
        ("&#x27;", "'"),
        ("&#x26;", "&"),
        ("&ndash;", "-"),
        ("&#64;", "@")]

    html = reduce(lambda a, b: re.sub(b[0], b[1], a), entities, html)
    return filter(lambda x: ord(x) > 9 and ord(x) < 127, html).strip()


def ensure_int(param):
    """Ensure the given param is an int"""
    try:
        param = re.sub("\W", "", param)
        return int(param)
    except ValueError:
        return None


def load_config(section, conf):
    """Load a config section"""
    return config.Config(conf, section)


def version(**kwargs):
    """Prepare the version string"""
    number = "0.5.5"
    git_file = ".git/refs/heads/master"
    git_path = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
            os.pardir, os.pardir, git_file))

    if "short" in kwargs:
        return number

    if not os.path.exists(git_path):
        git_path = os.getcwd() + "/" + git_file
        if not os.path.exists(git_path):
            git_path = os.getcwd() + "/../" + git_file
            if not os.path.exists(git_path):
                return "pyhole v%s - http://pyhole.org" % number

    with open(git_path, "r") as git:
        git_commit = git.read()
    git.closed

    if "long" in kwargs:
        return "%s-%s" % (number, git_commit[0:5])

    return "pyhole v%s (%s) - http://pyhole.org" % (number, git_commit[0:5])


def get_home_directory():
    """Return the home directory"""
    home_dir = os.getenv("HOME") + "/.pyhole/"
    if not os.path.exists(home_dir):
        os.makedirs(home_dir)

    return home_dir


def get_directory(new_dir):
    """Return a directory"""
    home_dir = get_home_directory()
    new_dir = home_dir + new_dir

    if not os.path.exists(new_dir):
        os.makedirs(new_dir)

    return new_dir + "/"


def write_file(dir, file, data):
    """Write data to file"""
    dir = get_directory(dir)

    with open(dir + file, "w") as f:
        f.write(str(data).strip())
    f.closed


def read_file(dir, file):
    """Read and return the data in file"""
    dir = get_directory(dir)

    try:
        with open(dir + file, "r") as f:
            data = f.read()
        f.closed

        return data
    except IOError:
        return None


def generate_config():
    """Generate an example config"""
    example = """# Global Configuration

[Pyhole]
admins: nick!ident, nick2!ident
command_prefix: .
reconnect_delay: 60
rejoin_delay: 5
debug: False
plugin_dir: /home/pyhole/plugins
plugins: admin, dice, entertainment, news, search, urls, weather

[Redmine]
domain: redmine.example.com
key: abcd1234

# IRC Network Configuration

[FreeNode]
server: verne.freenode.net
password:
port: 7000
ssl: True
ipv6: True
bind_to: fe80::1
nick: mynick
identify_password: mypass
channels: #mychannel key, #mychannel2

[EFnet]
server: irc.efnet.net
password:
port: 6667
ssl: False
ipv6: False
bind_to:
nick: mynick
identify_password:
channels: #mychannel key, #mychannel2
"""

    with open(get_home_directory() + "pyhole.conf", "w") as f:
        f.write(example)
    f.closed
