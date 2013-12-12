# Copyright 2008 Wyplay
# $Header: $

inherit git

DESCRIPTION="xutils test ebuild for a github environment"
HOMEPAGE="http://www.wyplay.com"

EGIT_BASE_URI="git@github.com:ptisserand"
EGIT_REPO_URI="hello-test-to-remove.git"
: ${EGIT_BRANCH:="master"}
: ${EGIT_REVISION:="de39571"}

LICENSE="Wyplay"
SLOT="0"
KEYWORDS="x86-host"
IUSE=""

DEPEND=""
RDEPEND=""

src_unpack() {
	git_src_unpack || die
}

src_install() {
	keepdir /usr/targets
}
