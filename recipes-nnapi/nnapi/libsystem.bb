DESCRIPTION = "Libsystem library from ChromeOs project"
LICENSE = "CLOSED"
HOMEPAGE = "https://chromium.googlesource.com/aosp/platform/system/core/+/15e8363d6289ccf3e60fd8b7bd29e9258ba82493/libsystem/"

TOOLCHAIN = "clang"

SRC_URI = " \
    file://libsystem.tar.gz \
    "

S = "${WORKDIR}"

do_install() {
    install -d ${D}${includedir}
    install -d ${D}${includedir}/aosp
    install -d ${D}${includedir}/aosp/
    cd ${S}
    cp -r ${S}/include/system  ${D}${includedir}/aosp/
}

FILES:${PN} = "${includedir}"
