import requests
import json
import subprocess
import tempfile
import os

class CoprSyncException(Exception):
    pass

def get_copr(username, coprname, apiurl):
    """ return JSON information about given copr. """

    coprs_url = "{}/coprs/{}".format(apiurl, username)

    resp = requests.get(coprs_url)
    if resp.status_code != 200:
        raise CoprSyncException("Unable to get list of coprs for {}".format(username))

    data = json.loads(resp.text)
    if "repos" in data:
        for copr in data["repos"]:
            if "name" in copr and copr["name"] == coprname:
                # got it!
                return copr

    raise CoprSyncException("No coprs received for user {}".format(username))


def generate_repo_config(copr, username):
    """ Generate temporary config for mrepo."""

    config = """
[main]
reposdir=

[{reponame}]
name={username}/{reponame}
baseurl={url}
gpgcheck=0
"""

    if "yum_repos" in copr:
        repos = copr["yum_repos"]
    else:
        raise CoprSyncException("Repo URL is missing, nothing to sync with")

    # generate repo configs
    repo_configs = {}
    for repo in repos:
        repo_configs[repo] = config.format(reponame=repo, username=username,
                                           url=repos[repo])

    return repo_configs


def run_reposync(configs, destdir):
    """ Run reposync and createrepo. """

    cmd = "reposync -c {cfg} -p {destdir} -r {repoid}" \
          "&& createrepo --database --update {destdir}/{repoid}"

    for config in configs:
        fd, tempcfg = tempfile.mkstemp()
        try:
            cfg = os.fdopen(fd, "w+")
            cfg.write(configs[config])
            cfg.flush()

            bash = subprocess.Popen(['bash'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE)
            command = cmd.format(cfg=tempcfg, destdir=destdir, repoid=config)
            _, stderr = bash.communicate(bytes(command, 'UTF-8'))

        finally:
            cfg.close()
            os.remove(tempcfg)

        if bash.returncode != 0:
            raise CoprSyncException("repo failed: {}".format(stderr))
