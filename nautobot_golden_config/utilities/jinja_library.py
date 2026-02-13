# Copyright (c) 2012-2013 Andrey Antukh <niwi@niwi.be>

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of copyright holders nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL COPYRIGHT HOLDERS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
from jinja2 import Environment


# Global register dict for third party
# template functions, filters and extensions.
_local_env = {
    "globals": {},
    "tests": {},
    "filters": {},
    "extensions": set(),
}


def update_env(env: Environment):
    """
    Given a jinja environment, update it with third party
    collected environment extensions.
    """

    env.globals.update(_local_env["globals"])
    env.tests.update(_local_env["tests"])
    env.filters.update(_local_env["filters"])

    for extension in _local_env["extensions"]:
        env.add_extension(extension)


def _attach_function(attr, func, name=None):
    if name is None:
        name = func.__name__

    global _local_env
    _local_env[attr][name] = func
    return func


def _register_function(attr, name=None, fn=None):
    if name is None and fn is None:

        def dec(func):
            return _attach_function(attr, func)

        return dec

    elif name is not None and fn is None:
        if callable(name):
            return _attach_function(attr, name)
        else:

            def dec(func):
                return _register_function(attr, name, func)

            return dec

    elif name is not None and fn is not None:
        return _attach_function(attr, fn, name)

    raise RuntimeError("Invalid parameters")


def extension(extension):
    global _local_env
    _local_env["extensions"].add(extension)
    return extension


def global_function(*args, **kwargs):
    return _register_function("globals", *args, **kwargs)


def test(*args, **kwargs):
    return _register_function("tests", *args, **kwargs)


def filter(*args, **kwargs):
    return _register_function("filters", *args, **kwargs)
