#!/usr/bin/env python

import os, sys, json, argparse
from six import print_
from six.moves import filter, reduce
from brew import ClientSession, PathInfo

BREWHUB_URL = {
		"stage": "",
		"prod": "https://",
}

parser = argparse.ArgumentParser()
parser.add_argument("container_build", help="name or id of container build to analyze")
parser_env = parser.add_mutually_exclusive_group()
parser_env.add_argument("-E", "--env", default="stage", help="brew environment (default: stage)")
parser_env.add_argument("--prod", action="store_const", dest="env", const="prod")
parser_env.add_argument("--stage", action="store_const", dest="env", const="stage")
args = parser.parse_args()

brew = ClientSession(BREWHUB_URL[args.env], opts={"krbservice": "brewhub"})
brew.krb_login()

# find component metadata
print_("loading build data from brew", file=sys.stderr)
buildinfo = brew.getBuild(args.container_build)
metadata_file = open(os.path.join(PathInfo().build(buildinfo), 'metadata.json'))

# flat list of all component dicts
components = reduce(lambda l, o: l + list(filter(lambda c: c["type"] == "rpm", o["components"])),
                    filter(lambda o: "components" in o,
                           json.load(metadata_file)["output"]),
                    [])
print_("found {0} components".format(len(components)), file=sys.stderr)


# format rpm name from component dict
def rpm_for(component):
    return "{name}-{version}-{release}.{arch}.rpm".format(**component)


# query brew for srpm from rpm name
def srpms_for(rpm):
    print_(".", end="", file=sys.stderr)
    try:
        rpminfo = brew.getRPM(rpm, strict=True)
    except:
        print_("failure for", rpm, file=sys.stderr)
        print_("component:", component, file=sys.stderr)
        raise
    try:
        buildrpms = brew.listBuildRPMs(rpminfo["build_id"])
    except:
        print_("failure for", rpm, file=sys.stderr)
        print_("component:", component, file=sys.stderr)
        print_("rpminfo:", rpminfo, file=sys.stderr)
        raise
    return list(map(rpm_for, (filter(lambda r: r["arch"] == "src", buildrpms))))


# list of unique rpms
rpms = set(map(rpm_for, components))
print_("found {0} rpms".format(len(rpms)), file=sys.stderr)
print_("\n".join(sorted(rpms)))

# list of unique srpms
print_("loading rpm data from brew", end="", file=sys.stderr)
srpms = set(reduce(lambda s, c: s + srpms_for(c), components, []))
print_("\nfound {0} srpms".format(len(srpms)), file=sys.stderr)
print_("\n".join(sorted(srpms)))

# vim: et sw=4 ts=4
