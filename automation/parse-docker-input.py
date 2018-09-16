#!/usr/bin/env python

#
# Parse yaml file and generates 'pub push-docker' commands
#
# Expected file format:
# ---
# repository: jboss-datagrid-6/datagrid65-openshift
# tags: 1.2-19,1.2,latest
# build: jboss-datagrid-6-datagrid65-openshift-docker-1.2-19
# ---
# repository: ...
#
# Contact: sgraf@redhat.com
#

import optparse
import subprocess
import sys
import yaml

def make_parser():
    parser = optparse.OptionParser()
    parser.add_option("--target", default="cdn-docker-stage")
    parser.add_option("--inputfile")
    parser.add_option("--ignoreerrors", action="store_true")
    return parser

def error(msg):
    """
    In case of error print message and exit with non-zero exit code.
    :param msg: message
    :return: None
    """
    print msg
    sys.exit(1)

def run(cmd):
    """
    Run command in shell.
    :param cmd: command to run
    :return: exit_code, output
    """
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    output, dummy = proc.communicate()
    return proc.returncode, output

if __name__ == "__main__":
    parser = make_parser()
    (parsed, _) = parser.parse_args()

    [exit_code, output] = run ("grep repository %s | awk '{ print $2 }' | sort | uniq -c | grep -v ' 1 '" % parsed.inputfile)
    if exit_code == 1:
        print "no dupe repositories = OK"
    else:
        if parsed.ignoreerrors:
            print "Dupe repositories found: %s" % output
        else:
            error("Dupe repositories found: %s" % output)

    [exit_code, output] = run ("grep tags %s | grep -v latest" % parsed.inputfile)
    if exit_code == 1:
        print "no tags without latest = OK"
    else:
        if parsed.ignoreerrors:
            print "Tags without latest found: %s" % output
        else:
            error("Tags without latest found: %s" % output)

    print
    stream = file(parsed.inputfile,'r')
    for data in yaml.load_all(stream):
        # pub push-docker --target $TARGET --repo $REPO --tag $TAG $NVR
        push_string="pub push-docker"
        push_string+=" --target %s" % parsed.target
        repository = "redhat-%s-%s" % (data['repository'].split('/')[0],
                                       data['repository'].split('/')[1], )
        push_string+=" --repo %s" % repository
        for tag in data['tags'].split(','):
            push_string+=" --tag %s" % tag
        push_string+=" --nowait"
        #push_string+=" --task-id-file=push_%s_%s" % (TARGET, repository)
        push_string+=" %s" % data['build']
        print push_string

