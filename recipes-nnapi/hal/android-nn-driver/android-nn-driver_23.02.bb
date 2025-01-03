SUMMARY = "ARM Neural Network SDK"
DESCRIPTION = "Linux software and tools to enable machine learning Tensorflow lite workloads on power-efficient devices"
LICENSE = "MIT & Apache-2.0"
# Apache-2.0 license applies to mobilenet tarball
LIC_FILES_CHKSUM = "file://LICENSE;md5=3e14a924c16f7d828b8335a59da64074 \
                    file://${COMMON_LICENSE_DIR}/Apache-2.0;md5=89aea4e17d99a7cacdbeed46a0096b10"

PV_MAJOR = "${@d.getVar('PV',d,1).split('.')[0]}"
PV_MINOR = "${@d.getVar('PV',d,1).split('.')[1]}"

PROVIDES = "virtual/libvendor-nn-hal"
RPROVIDES:${PN} = "libvendor-nn-hal"

TOOLCHAIN = "clang"

SRCREV = "084cb4dcb9eca3eac3fc634f052ddb7d7fcc0bb4"
BRANCH = "branches/android-nn-driver_${PV_MAJOR}_${PV_MINOR}"

SRC_URI = "git://github.com/ARM-software/android-nn-driver.git;protocol=https;branch=${BRANCH} \
           file://0001-don-t-use-__system_properties.patch \
           file://0002-use-syncWait-instead-of-sync_wait.patch \
           file://0003-add-missing-cfloat-include.patch \
           file://0004-add-Makefile.patch \
           file://0005-add-gpu-tuning-file-support.patch \
           file://0006-android-nn-driver-link-libarmnnSerializer.patch \
           file://0007-replace-steady_clock-by-high_resolution_clock.patch \
           file://0008-Add-fcntl-include-depedency-for-1.2-1.3-armnndriveri.patch \
           file://0009-Add-float-dependency-for-armnndriverimpl.patch \
           file://0010-Fix-a-wrong-implicit-type-cast.patch \
           "

S = "${WORKDIR}/git"

DEPENDS = " armnn nnapi-headers nnapi-support opencl-headers opencl-clhpp fmt "
DEPENDS += " ${@bb.utils.contains('TFLITE_PREBUILT', '1', 'tensorflowlite-prebuilt', 'tensorflow-lite', d)} "

TUNE_CCARGS:remove = "-mcpu=cortex-a73.cortex-a53"

EXTRA_OEMAKE = " \
    'NNAPI_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/nnapi' \
    'AOSP_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/aosp' \
    'EIGEN_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/eigen' \
    'GEMMLOWP_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/tensorflow/lite/tools/make/downloads/gemmlowp/' \
    'LIBTEXTCLASSIFIER_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/libtextclassifier/' \
    'ARMNN_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/armnn/' \
    'ARMNN_UTILS_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/armnnUtils/' \
    'ROOT_DIR_INCLUDE=${S}/' \
"

do_install() {
    oe_runmake install DESTDIR=${D} LIBDIR=${libdir} INCLUDEDIR=${includedir}
}
