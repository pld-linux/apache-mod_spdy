# NOTE:
# - apache 2.4 patch https://code.google.com/p/mod-spdy/issues/detail?id=64
#   and a fork (due lack of response in upstream): https://github.com/eousphoros/mod-spdy
# - donated to asf http://googledevelopers.blogspot.com/2014/06/modspdy-is-now-apache-project.html
#   whose repo is at https://svn.apache.org/repos/asf/httpd/mod_spdy/trunk/
#
# Conditional build:
%bcond_with	werror		# build with "-Werror" enabled

%define		mod_name	spdy
%define 	apxs		%{_sbindir}/apxs
Summary:	Apache module to enable SPDY support
Name:		apache-mod_%{mod_name}
Version:	0.9.3.3
Release:	1
License:	Apache v2.0
Group:		Daemons
Source0:	mod-spdy-%{version}.tar.xz
# Source0-md5:	35770e4855b2953440be5a56d9da3fa4
Source1:	get-source.sh
Source2:	gclient.conf
Patch0:		gyp.patch
Patch1:		log-constants.patch
Patch2:		apache2.4.patch
Patch3:		system-zlib.patch
URL:		http://code.google.com/p/mod-spdy/
BuildRequires:	%{apxs}
BuildRequires:	apache-devel >= 2.2
BuildRequires:	minizip-devel
BuildRequires:	tar >= 1:1.22
BuildRequires:	xz
Requires:	apache(modules-api) = %apache_modules_api
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_pkglibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define		_pkgrootdir	%(%{apxs} -q SYSCONFDIR 2>/dev/null)
%define		_sysconfdir	%{_pkgrootdir}/conf.d

%description
mod_spdy is an Apache module that allows an Apache server to support
the SPDY protocol for serving HTTP resources.

%prep
%setup -q -n mod-spdy-%{version}
%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1

%build
CC="%{__cc}" \
CXX="%{__cxx}" \
%{__python} build/gyp_chromium \
	--format=make \
	--depth=. \
	build/all.gyp \
	%{!?with_werror:-Dwerror=} \
	-Duse_openssl=1 \
	-Duse_system_apache_dev=1 \
	-Duse_system_libjpeg=1 \
	-Duse_system_libpng=1 \
	-Duse_system_opencv=1 \
	-Duse_system_zlib=1 \
	-Dsystem_include_path_apr=%{_includedir}/apr \
	-Dsystem_include_path_aprutil=%{_includedir}/apr-util \
	-Dsystem_include_path_httpd=%{_includedir}/apache \
	%{nil}

%{__make} mod_spdy \
	BUILDTYPE=%{!?debug:Release}%{?debug:Debug} \
	%{?with_verbose:V=1} \
	CC="%{__cc}" \
	CXX="%{__cxx}" \
	CC.host="%{__cc}" \
	CXX.host="%{__cxx}" \
	LINK.host="%{__cxx}" \
	CFLAGS="%{rpmcflags} %{rpmcppflags}" \
	CXXFLAGS="%{rpmcxxflags} %{rpmcppflags}" \
	%{nil}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_pkglibdir},%{_sysconfdir}}

out=out/%{!?debug:Release}%{?debug:Debug}
install -p $out/libmod_%{mod_name}.so $RPM_BUILD_ROOT%{_pkglibdir}/mod_%{mod_name}.so

cat > $RPM_BUILD_ROOT%{_sysconfdir}/90_mod_%{mod_name}.conf <<EOF
LoadModule %{mod_name}_module	modules/mod_%{mod_name}.so
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%post
%service -q httpd restart

%postun
if [ "$1" = "0" ]; then
	%service -q httpd restart
fi

%files
%defattr(644,root,root,755)
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/*_mod_%{mod_name}.conf
%attr(755,root,root) %{_pkglibdir}/mod_%{mod_name}.so
