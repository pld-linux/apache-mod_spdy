#!/bin/sh
# Usage:
# ./get-source.sh
# Author: Elan Ruusamäe <glen@pld-linux.org>
#
# http://code.google.com/p/mod-spdy/wiki/GettingStarted

package=mod-spdy
baseurl=http://modpagespeed.googlecode.com/svn
baseurl=http://mod-spdy.googlecode.com/svn
# leave empty to use latest tag, or "trunk" for trunk
version=
spec=apache-mod_spdy.spec
force=0

# abort on errors
set -e
# work in package dir
dir=$(dirname "$0")
cd "$dir"

if [[ "$1" = *force ]]; then
	force=1
	shift
fi

if [ "$1" ]; then
	version=$1
fi

if [ -z "$version" ]; then
	echo "Looking for latest version..."
	version=$(svn ls $baseurl/tags/ | grep '^[0-9]' | sort -V | tail -n1)
	version=${version%/}
fi

if [ "$version" = "trunk" ]; then
	echo "Using trunk"
	svnurl=$baseurl/trunk/src
	version=$(date +%Y%m%d)
else
	echo "Version: $version"
	svnurl=$baseurl/tags/$version/src
fi

release_dir=$package-$version
tarball=$release_dir.tar.xz

if [ -f $tarball -a $force != 1 ]; then
	echo "Tarball $tarball already exists"
	exit 0
fi

# gclient needs python 2.6
if python -c "import sys; sys.exit(sys.version[:3] > '2.6')"; then
	echo >&2 "Need python >= 2.6 for gclient"
	exit 1
fi

topdir=${PWD:-($pwd)}

gclient=$(which gclient 2>/dev/null)
if [ -z "$gclient" ]; then
	# http://www.chromium.org/developers/how-tos/install-depot-tools
	test -d depot_tools || {
		# could also checkout:
		# svn co http://src.chromium.org/svn/trunk/tools/depot_tools
		wget -c https://src.chromium.org/svn/trunk/tools/depot_tools.zip
		unzip -qq depot_tools.zip
		chmod a+x depot_tools/gclient depot_tools/update_depot_tools
	}
	gclient=$topdir/depot_tools/gclient
fi

gclientfile=$topdir/gclient.conf
install -d $package
cd $package

if [ ! -f $gclientfile ]; then
	# create initial config that can be later modified
	$gclient config $svnurl --gclientfile=$gclientfile
fi

cp -p $gclientfile .gclient

# emulate gclient config, preserving our deps
sed -i -re '/"url"/ s,"http[^"]+","'$svnurl'",' .gclient

$gclient sync --nohooks -v

# Populate the LASTCHANGE file template as we will not include VCS info in tarball
(cd src && svnversion > LASTCHANGE.in)
cd ..

cp -al $package/src $release_dir
XZ_OPT=-e9 tar -caf $tarball --exclude-vcs $release_dir
rm -rf $release_dir

../md5 $spec
../dropin $tarball &
