DESCRIPTION = "NNAPI support library for Linux - This is a port on yocto from chromeos"
LICENSE = "CLOSED"
HOMEPAGE = "https://chromium.googlesource.com/chromiumos/platform2/+/HEAD/nnapi"

# Recipe adapted from https://chromium.googlesource.com/chromiumos/overlays/chromiumos-overlay/+/refs/heads/main/chromeos-base/nnapi/nnapi-0.0.2-r2.ebuild

TOOLCHAIN = "clang"

BRANCH_NAME = "master"

SRC_URI = " \
    git://chromium.googlesource.com/chromiumos/platform2/;protocol=https;branch=main;rev=85109a843d7310588ec7feea6775ace121125882 \
    git://chromium.googlesource.com/aosp/platform/frameworks/native;protocol=https;branch=${BRANCH_NAME};rev=23e2bf511667b4fa5859812a4e7945c8638f6603;destsuffix=git/aosp_libs/libnative \
    git://chromium.googlesource.com/aosp/platform/system/core/libcutils;protocol=https;branch=${BRANCH_NAME};rev=ab4ff9c1ded692a3529e9c03ea6943fe094df0f9;destsuffix=git/aosp_libs/libcutils \
    git://chromium.googlesource.com/aosp/platform/system/core/libutils;protocol=https;branch=${BRANCH_NAME};rev=a14d63edf6f0058f6c478093b8e90e35fa3314ec;destsuffix=git/aosp_libs/libutils \
    git://chromium.googlesource.com/aosp/platform/system/libbase;protocol=https;branch=${BRANCH_NAME};rev=b7f8cf0f0beab62bc5a391226ebd835c2fe377dc;destsuffix=git/aosp_libs/libbase \
    git://chromium.googlesource.com/aosp/platform/system/libfmq;protocol=https;branch=${BRANCH_NAME};rev=8e369832671de86e05cbbd3eeb7ddfe7df95f1ec;destsuffix=git/aosp_libs/libfmq \
    git://chromium.googlesource.com/aosp/platform/system/libhidl;protocol=https;branch=${BRANCH_NAME};rev=6b79fa280312109216ce8b3a4893f266775cddc2;destsuffix=git/aosp_libs/libhidl \
    git://chromium.googlesource.com/aosp/platform/system/logging;protocol=https;branch=${BRANCH_NAME};rev=e386a40d816e794c12040936608d252ab96077a7;destsuffix=git/aosp_libs/logging \
    file://00001-libbase-fix-stderr-logging.patch \
    file://00002-libhidl-callstack.patch \
    file://00003-libutils-callstack.patch \
    file://00004-libfmq-page-size.patch \
    file://00005-libcutils-ashmemtests.patch\
    file://00006-libhidl-cast-interface.patch \
    file://00007-libbase-get-property-from-envvar.patch \
    file://00008-libutils-memory-leak.patch \
    file://00009-libutils-timer-cast.patch \
    file://0001-libbase-add-Makefile.patch \
    file://0001-libcutils-fix-some-minor-compilation-issues.patch \
    file://0002-libcutils-add-Makefile.patch \
    file://0001-libfmq-add-missing-climits-include.patch \
    file://0002-libfmq-add-missing-memory-include.patch \
    file://0003-libfmq-add-Makefile.patch \
    file://0001-liblog-add-Makefile.patch \
    file://0001-libutils-add-missing-include.patch \
    file://0002-libutils-add-Makefile.patch \
    file://0001-libhidl-add-Makefile.patch \
    file://0001-libnative-add-__BIONIC__-guard-on-__assert.patch \
    file://0001-libnnapi-support-add-missing-include.patch \
    file://0002-libnnapi-support-add-Makefile.patch \
    file://0003-libnnapi-support-Makefile-install-missing-header-ui-.patch \
    file://0004-libnnapi-support-Makefile-install-missing-header-nat.patch \
    file://0005-libnnapi-support-Makefile-install-missing-libhardwar.patch \
    file://0006-libnnapi-support-Makefile-install-missing-hidl-heade.patch \
    file://0007-libnnapi-support-Makefile-install-missing-binder-hea.patch \
    file://0008-libnnapi-support-add-missing-generated-files.patch \
    file://libnnapi-support-add-extern-c.patch \
    "

S = "${WORKDIR}/git"

TUNE_CCARGS:remove = "-mcpu=cortex-a73.cortex-a53"

do_install() {
    oe_runmake install DESTDIR=${D} LIBDIR=${libdir} INCLUDEDIR=${includedir}
}

SOLIBS = ".so"
FILES_SOLIBSDEV = ""
FILES:${PN} = "${libdir}/* ${includedir}"
