DESCRIPTION = "A library for on-device text classification (address, telephone number, emails etc.). This is a port to yocto from chromeos"
LICENSE = "CLOSED"
HOMEPAGE = "https://chromium.googlesource.com/chromiumos/third_party/libtextclassifier/"

TOOLCHAIN = "clang"

BRANCH_NAME = "release-R85-13310.B"

SRC_URI = " \
    git://chromium.googlesource.com/chromiumos/third_party/libtextclassifier;protocol=https;branch=${BRANCH_NAME} \
    "
SRCREV = "${AUTOREV}"

S = "${WORKDIR}/git"

do_compile() {
}

do_install() {
    install -d ${D}${includedir}
    install -d ${D}${includedir}/libtextclassifier
    cd ${S}
    for file in $(find . -name '*.h'); do
        install -d "${D}${includedir}/libtextclassifier/$(dirname -- "${file}")"
        install -m 0644 "${file}" "${D}${includedir}/libtextclassifier/${file}"
    done
}

FILES:${PN} = "${includedir}"
