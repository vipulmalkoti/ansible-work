#!/bin/sh

#----------------------------------------------------------------------------------------------------------------
# Author: vmalkoti
#----------------------------------------------------------------------------------------------------------------

if [ $# -ne 1 ]
then
  echo $#
  echo "Usage: $0 <file-name>"
  echo "Please try again with the appropriate parameters"
  exit 1
fi

OUT=/tmp/mvp.ip.$$

if [ -f $1 ]
then
	awk '/FAILED/ {print $2}' $1 >$OUT
else
	echo '$1 not found'
fi

echo $OUT
DATE=`date +%Y-%m-%d`

if [ -f impacted_containers_$DATE.csv ]
then
	rm impacted_containers_$DATE.csv
fi

if [ -f container_repo_list_$DATE.csv ]
then
	rm container_repo_list_$DATE.csv
fi

if [ -f container_repos_not_migrated_$DATE.csv ]
then
	rm container_repos_not_migrated_$DATE.csv
fi

if [ -f containers_with_dockerref_$DATE.csv ]
then
	rm containers_with_dockerref_$DATE.csv
fi

echo "Repo Name,Branch Name,Product" >> impacted_containers_$DATE.csv

while read REPO
do
	BRANCH=${REPO##*=}
	case $BRANCH in
		3scale-*|rhamp-*) PRODUCT="3Scale" ;;
		*extras-rhel*) PRODUCT="RHEL Extras" ;;
		rhaos-*|rhose-*|rhcda-*) PRODUCT="OpenShift (Except OSO)" ;;
		rhel-*) PRODUCT="RHEL" ;;
		cdk*) PRODUCT="CDK" ;;
		jb-mm-*|jb-cs-mgmt7-*) PRODUCT="JBMM" ;;
		cfme-*) PRODUCT="CFME";;
		devtoolset-*|devtools-*) PRODUCT="DTS" ;;
		*e2e*) PRODUCT="Release E2E" ;;
		rhscl-*) PRODUCT="SCL" ;;
		*amq-*) PRODUCT="(xPaaS) AMQ" ;;
		*amqmaas*) PRODUCT="AMQ Online" ;;
		ce-*-jdk|ce-*-rhel|jb-rhel*|jdk-*|ce-*-openshift-openjdk-*|jb-dev*|jb-openjdk*) PRODUCT="(xPaaS) Base Image" ;;
		*-datagrid*) PRODUCT="(xPaaS) JDG" ;;
		*-datavirt*) PRODUCT="(xPaaS) JDV" ;;
		*-decisionserver-*|*-processserver*|*kieserver*) PRODUCT="(xPaaS) BRMS/BPMSuite" ;;
		*-rdhm-*) PRODUCT="RHDM" ;;
		*-eap*) PRODUCT="(xPaaS) EAP" ;;
		*-webserver*) PRODUCT="(xPaaS) JWS" ;;
		*-sso*) PRODUCT="(xPaaS) RH-SSO" ;;
		fis-*|fuse-*) PRODUCT="Fuse" ;;
		rhos-*) PRODUCT="OpenStack" ;;
		eng-*|jenkins-*|osbs-*) PRODUCT="RedHat Internal" ;;
		rhevm-*) PRODUCT="RHV" ;;
		rhcert-*) PRODUCT="RedHat Certification" ;;
		dotnet-*) PRODUCT="dotNET" ;;
		ceph-*) PRODUCT="Ceph" ;;
		rhgs-*) PRODUCT="RHGS" ;;
		rhmap-*|jb-map-*) PRODUCT="RHMAP" ;;
		ansible-tower*) PRODUCT="Ansible Tower" ;;
		rhoar-*) PRODUCT="RHOAR" ;;
		online-*|*libra-*) PRODUCT="OpenShift Online" ;;
		automation-extras-*) PRODUCT="Openscap" ;;
		*istio*) PRODUCT="ISTIO" ;;
		*) PRODUCT="Unknown" ;;
	esac
	#reponame=`awk -F "/" '{print $6' $REPO`
	echo $REPO","$BRANCH","$PRODUCT >> impacted_containers_$DATE.csv
done <$OUT

echo "Repo Name,Branch Name,Product" >> container_repo_list_$DATE.csv
cat impacted_containers_$DATE.csv| tr "," "/" | awk -F "/" '{print $5"/"$6","$9","$10}' | sort -u >> container_repo_list_$DATE.csv

echo "Repo Name,Branch Name,Product" >> container_repos_not_migrated_$DATE.csv
echo "Repo Name,Branch Name,Product" >> containers_with_dockerref_$DATE.csv

grep '^rpms' container_repo_list_$DATE.csv >> container_repos_not_migrated_$DATE.csv
grep -vf container_repo_blacklist.csv container_repo_list_$DATE.csv | grep -v rpms >> containers_with_dockerref_$DATE.csv
#exit 0
