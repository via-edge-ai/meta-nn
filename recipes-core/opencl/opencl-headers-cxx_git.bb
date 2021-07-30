SUMMARY  = "OpenCL API C++ Headers"
DESCRIPTION = "OpenCL C++ API headers from Khronos Group"
LICENSE  = "Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE.txt;md5=3b83ef96387f14655fc854ddc3c6bd57"

S = "${WORKDIR}/git"

SRCREV = "2ba05c4d2173db2536f5a157ff94afa8bb355016"
SRC_URI = "git://github.com/KhronosGroup/OpenCL-CLHPP.git;protocol=https"

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install () {
    install -d ${D}${includedir}/CL/
    install -m 0644 ${S}/include/CL/*.hpp ${D}${includedir}/CL
}
