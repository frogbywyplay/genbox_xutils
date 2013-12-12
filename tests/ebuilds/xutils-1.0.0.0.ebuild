# Copyright 2008 Wyplay
# $Header: $

inherit mercurial distutils

DESCRIPTION="Genbox-ng utils"
HOMEPAGE="http://www.wyplay.com"

EHG_REPO_URI="genbox/genbox-tools/$PN"
: ${EHG_BRANCH:="default"}

LICENSE="Wyplay"
SLOT="0"
KEYWORDS="x86-host"
IUSE=""

DEPEND="dev-python/setuptools"
RDEPEND=">=dev-lang/python-2.5
	sys-config/genbox-config"

src_unpack() {
	     mercurial_src_unpack || die
}

src_install() {
	distutils_src_install
	keepdir /usr/targets
}
