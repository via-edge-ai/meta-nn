require xtensa-ann.inc

TOOLCHAIN = "clang"

SRCREV = "af2acee46215adb60b997b682ae6b9b71481b725"

BRANCH = "mtk-android-11"

SRC_URI += "git://gitlab.com/mediatek/aiot/team-baylibre/xtensa_ann.git;protocol=https;branch=${BRANCH} \
           file://0001-xtensa-ann-fix-compilation-issues.patch \
           file://0002-xtensa-ann-add-wrapper-for-nnapi.patch \
           file://0003-xtensa-ann-add-Makefile.patch \
           file://0001-xtensa_driver-concat-skip-optimization-to-avoid-segf.patch \
           file://0001-xtensa-ann-fix-link-issue.patch \
           "

S = "${WORKDIR}/git"

DEPENDS = " \
    ${@bb.utils.contains('TFLITE_PREBUILT', '1', 'tensorflowlite-prebuilt', 'tensorflow-lite', d)} \
    libapu \
    nnapi-headers \
    nnapi-support \
    libsystem \
"

RDEPENDS:${PN} = " \
    nnapi-support \
    ${@bb.utils.contains('TFLITE_PREBUILT', '1', 'tensorflowlite-prebuilt', 'tensorflow-lite', d)} \
"

TUNE_CCARGS:remove = "-mcpu=cortex-a73.cortex-a53"

EXTRA_OEMAKE = " \
    'NNAPI_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/nnapi' \
    'AOSP_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/aosp' \
    'EIGEN_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/eigen' \
    'GEMMLOWP_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/tensorflow/lite/tools/make/downloads/gemmlowp/' \
    'LIBTEXTCLASSIFIER_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/libtextclassifier/' \
    'LIBAPU_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/libapu' \
    'SYSROOT=${STAGING_DIR_TARGET}' \
    'LIBDIR=${libdir}' \
"

do_install:append() {
    oe_runmake install DESTDIR=${D} LIBDIR=${libdir} INCLUDEDIR=${includedir}
}
