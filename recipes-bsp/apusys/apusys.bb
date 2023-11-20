DESCRIPTION = "Mediatek APUSYS Out-of-tree kernel driver"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=16de935ebcebe2420535844d4f6faefc"

inherit module

SRCREV = "ce53cbf9e704d777a2b38b0ffdcf62315b0636bd"

BRANCH = "android13"

SRC_URI += "git://gitlab.com/mediatek/aiot/bsp/mtk-apusys-driver.git;protocol=https;branch=${BRANCH} \
"

S = "${WORKDIR}/git"

# The inherit of module.bbclass will automatically name module packages with
# "kernel-module-" prefix as required by the oe-core build environment.

RPROVIDES_${PN} += "kernel-module-apusys"