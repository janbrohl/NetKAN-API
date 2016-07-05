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
import cherrypy

id_chars = string.ascii_letters + string.digits + "-"

with open("config.json", "r", encoding="utf8") as f:
    config = json.load(f)
    u = config["username"]
    p = config["password"]
    target = config["target"]


def validate_unsafe(realm, username, password):
    cp = config["users"]
    return realm == config["realm"] and username in cp and cp["user"] == password

if not os.path.isdir("NetKAN"):
    subprocess.check_call(
        "git clone https://%s:%s@github.com/kan-api/NetKAN.git NetKAN" % (u, p), shell=True)

os.chdir("NetKAN")


def lock_file(path):
    return contextlib.closing(zc.lockfile.LockFile(path))


def write(identifier, obj, msg):
    if not all(c in id_chars for c in identifier):
        raise ValueError()
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent="\t")
    fp = os.path.join("NetKAN", "%s.netkan" % identifier)
    with lock_file("../netkan.lock"):
        if os.path.exists(fp):
            mode = "Edit"
        else:
            mode = "Add"
        r = int(time.time() * 100)
        subprocess.check_call("git checkout master", shell=True)
        subprocess.check_call("git branch %s-%x" % (u, r), shell=True)
        subprocess.check_call("git checkout kan-api-%x" % r, shell=True)
        with open(fp, "w", encoding="utf8") as f:
            f.write(s)
        subprocess.check_call("git add -A", shell=True)
        subprocess.check_call("git commit -m \"%sed %s\"" %
                              (mode, identifier), shell=True)
        subprocess.check_call(
            "git push --set-upstream origin %s-%x" % (u, r), shell=True)
        gh = github.GitHub(username=u, password=p)
        gh.repos(target)("NetKAN").pulls.post(title="%s %s" % (
            mode, identifier), head="%s:%s-%x" % (u, u, r), base="master", body=str(msg))
        subprocess.check_call("git checkout master", shell=True)


@cherrypy.popargs("identifier")
class Root:

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def netkan(self, identifier):
        data = cherrypy.request.json
        write(identifier, data["entry"], data["message"])
        return

cp_conf = {"/": {
    'tools.auth_basic.on': True,
    'tools.auth_basic.realm': config["realm"],
    'tools.auth_basic.checkpassword': validate_unsafe
}}

cherrypy.quickstart(Root(), "/", cp_conf)
