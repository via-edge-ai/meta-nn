SUMMARY = "Memory Efficient Serialization Library - Python3 Modules"
HOMEPAGE = "https://github.com/google/flatbuffers"
SECTION = "console/tools"
LICENSE = "Apache-2.0"

LIC_FILES_CHKSUM = "file://../LICENSE;md5=3b83ef96387f14655fc854ddc3c6bd57"

SRCREV = "0100f6a5779831fa7a651e4b67ef389a8752bd9b"
SRC_URI = "git://github.com/google/flatbuffers.git;branch=master;protocol=https"
S = "${WORKDIR}/git/python"

RDEPENDS:${PN} = "flatbuffers"

inherit setuptools3

