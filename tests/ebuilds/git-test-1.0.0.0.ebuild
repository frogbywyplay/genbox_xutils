# Copyright 2008 Wyplay
# $Header: $

inherit git distutils

DESCRIPTION="Genbox-ng utils"
HOMEPAGE="http://www.wyplay.com"

EGIT_BASE_URI="ssh://git.wyplay.int/var/lib/git/"
EGIT_REPO_URI="kernel-wyplay-2.6.23.y.git"
: ${EGIT_BRANCH:="master"}

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
