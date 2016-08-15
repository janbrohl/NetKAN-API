#!/usr/bin/env python3

#    Copyright (c) 2016, Jan Brohl <janbrohl@t-online.de>
#    All rights reserved.
#    See LICENSE.txt

import subprocess
import os
import os.path
import github
import json
import time
import contextlib
import zc.lockfile
import string
import bottle
import jsonrpc

id_chars = string.ascii_letters + string.digits + "-"

with open("config.json", "r", encoding="utf8") as f:
    config = json.load(f)
    u = config["username"]
    p = config["password"]
    target = config["target"]

if not os.path.isdir("NetKAN"):
    subprocess.check_call("git", "clone",
                          "https://%s:%s@github.com/%s/NetKAN.git NetKAN" % (u, p, u), shell=True)

os.chdir("NetKAN")


def lock_file(path):
    return contextlib.closing(zc.lockfile.LockFile(path))


def write(identifier, obj, msg, name, email):
    if not all(c in id_chars for c in identifier):
        raise ValueError()
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent="\t")
    fp = os.path.join("NetKAN", "%s.netkan" % identifier)
    with lock_file("../netkan.lock"):
        if os.path.exists(fp):
            mode = "Edit"
        else:
            mode = "Add"
        t = time.gmtime()
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        branch = "%s-%x" % (u, int(t * 1000))
        subprocess.check_call("git", "checkout",
                              "master", shell=True)
        subprocess.check_call("git", "branch",
                              branch, shell=True)
        subprocess.check_call("git", "checkout",
                              branch, shell=True)
        with open(fp, "w", encoding="utf8") as f:
            f.write(s)
        subprocess.check_call("git", "add",
                              "-A", shell=True)
        subprocess.check_call("git", "commit",
                              "-m", "%sed %s" % (mode, identifier),
                              "--author=%s <%s>" % (name, email),
                              shell=True)
        subprocess.check_call("git", "push",
                              "--set-upstream", "origin", branch, shell=True)
        gh = github.GitHub(username=u, password=p)
        gh.repos(target)("NetKAN").create_pull(
            title="%s %s at %s" % (
                mode, identifier, ts),
            head="%s:%s" % (u, branch),
            base="master",
            body=str(msg))


def auth(username=None, password=None, access_token=None):
    gh = github.GitHub(username=username, password=password,
                       access_token=access_token)
    user = gh.get_user()
    return user.name, user.email, user.login


def auth_write(identifier, auth_data, entry, msg):
    name, email, _login = auth(**auth_data)
    write(identifier, entry, msg, name, email)


def rpc(dispatcher, max_body_size=1 << 20):
    r = bottle.request
    ctype = r.content_type
    clen = r.content_length
    if ctype in ('application/json', 'application/json-rpc'):
        if 0 < clen <= max_body_size:
            data = r.body.read(clen)
            out = jsonrpc.JSONRPCResponseManager.handle(data, dispatcher)
            bottle.response.content_type = 'application/json'
            return out
    return None

app = bottle.Bottle()


@app.post("/<identifier>/")
def entry(self, identifier):
    dispatcher = {"write": (lambda *args: auth_write(identifier, *args))}
    return rpc(dispatcher)
