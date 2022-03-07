DESCRIPTION = "NNAPI support library for Linux - This is a port on yocto from chromeos"
LICENSE = "CLOSED"
HOMEPAGE = "https://chromium.googlesource.com/aosp/platform/frameworks/ml/+/refs/heads/master/nn/"

#Recipe adapted from https://chromium.googlesource.com/chromiumos/overlays/chromiumos-overlay/+/d6a2f18398235a000be954954f8c596ad8e4478b/chromeos-base/aosp-frameworks-ml-nn/aosp-frameworks-ml-nn-0.0.1-r166.ebuild

TOOLCHAIN = "clang"

BRANCH_NAME = "master"

SRC_URI = " \
    git://chromium.googlesource.com/aosp/platform/frameworks/ml;protocol=https;branch=master;rev=b2ff2115ebba168c055b3aa9719ed7951574abb3 \
    file://0001-nnapi-add-missing-includes.patch \
    file://0001-nnapi-add-optional-include.patch \
    "

S = "${WORKDIR}/git"

TUNE_CCARGS:remove = "-mcpu=cortex-a73.cortex-a53"
