#!/usr/bin/env python
import os, subprocess, argparse, sys, re

### Input
# Take in Environment (matches dock-pulp env names)
#         Repo Name (Only supports one repo for now)
#         Existing tag the image has you'd like to add a tag to

# Dict to Map Envs to Registries
registries = {'brew-qa' : 'brew-pulp-docker01.web.qa.ext.phx1.redhat.com:8888', 'brew-prod' : 'brew-pulp-docker01.web.prod.ext.phx2.redhat.com:8888', 'qa' : 'crane01.web.qa.ext.phx1.redhat.com', 'stage' : 'registry.access.stage.redhat.com', 'prod' : 'crane01.web.prod.ext.phx2.redhat.com'}

def getContainerInfo(server, repo, tag):
    """
    Take in the server, repo and tag you're searching with
    Return a tuple contianing the unedited lines from dockpulp that contain the docker v1 hash and the v2 digest of the image you're tagging
    Requires you to be logged in to dockpulp
    """
    
    # Query Dock Pulp
    p = subprocess.Popen(['dock-pulp', '--server', server, 'list', '-c', repo], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result, err = p.communicate()
    if err:
        print err
        sys.exit(1)

    # Search output for the given tag and check if it's a v2 hash or v1 and separate
    v1lines = []
    v2lines = []

    regex = re.compile(tag)
    v2regex = re.compile('sha256')

    print "Old Tag: {0}".format(tag)
    for line in result.split('\n'):
        if regex.search(line):
            if v2regex.search(line): 
                v2lines.append(line)
            else:
                v1lines.append(line)

    # Check that you found something
    if not v1lines or not v2lines:
        print "Tag: {0} not found in repo".format(tag)
        sys.exit(1)

    # Prune V2 Lines to only active
    active = re.compile('active')
    for line in v2lines:
        if not active.search(line):
            v2lines.remove(line)

    # Check that you have only 1 of each v1 and v2 left
    if len(v1lines) > 1 or len(v2lines) > 1:
        print "Still too many hashes"
        sys.exit(1)
        
    return (v1lines[0], v2lines[0])

def getTags(inittag, hashLine):
    """
    Take in the line from dockpulp which contains the tags, in the format '.*(tags: $tag1, $tag2, $tagn)$'
       And string that contains tag to add
    Return list of tags
    """
    isTag = False
    tags = [inittag]

    for word in hashLine.split(): #[2] is the list of tags format '(tags: $tag1, $tag2, $tagn)'
        if isTag == False and word.strip('(),:') == 'tags':
            isTag = True
        elif isTag == True:
            tags.append(word.strip('(),'))
    return tags
    
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--server', dest='server', action="store", required=True)
    parser.add_argument('--repo', dest='repo', action="store", required=True)
    parser.add_argument('--old-tag', dest='oldtag', action="store", required=True)
    parser.add_argument('--new-tag', dest='newtag', action="store", required=True)
    args = parser.parse_args()

    # Sanity check parameters
    if not args.server in registries.keys():
        print "Invalid server specified, pick one of the following:"
        for server in registries.keys():
            print server
        sys.exit(1)

    v1hashline, v2hashline = getContainerInfo(args.server, args.repo, args.oldtag)

    v1hash = v1hashline.split()[1] # [0] is INFO [1] is the hash
    v2hash = v2hashline.split()[2] # [0] is INFO [1] is Manifest [2] is the hash

    # Now we know that the V1 Hash has all the tags that you want to preserve, because that's how tags for v1 are tracked, let's extract those
    tags = getTags(args.newtag, v1hashline)

    print tags
                        
    cmd = ["pub", "tag-docker", "--target", "cdn-docker-{0}".format(args.server), "--repo", args.repo, "--registry", registries[args.server], "--image-id", v1hash, "--digest", v2hash]
    # Add the necessary tags
    for tag in tags:
        cmd.append("--tag")
        cmd.append(tag)

    print "About to run the following: "
    print " ".join(cmd)
    nothing = raw_input("Are you sure? ")
    
    # Run command with subprocess
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result, err = p.communicate()
    if err:
        print err
        sys.exit(1)
    else:
        print "Tagging Successful!"
if __name__ == '__main__':
    main()
