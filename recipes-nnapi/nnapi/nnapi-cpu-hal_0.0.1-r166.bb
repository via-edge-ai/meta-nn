require nnapi-0.0.1-r166.inc

DEPENDS += " \
    ${@bb.utils.contains('TFLITE_PREBUILT', '1', 'tesorflowlite-prebuilt', 'tensorflow-lite', d)} \
    nnapi-support \
"

PROVIDES = "virtual/libvendor-nn-hal"
RPROVIDES:${PN} = "libvendor-nn-hal"

SRC_URI +=" \
    file://0001-Add-Makefile.patch \
    "

EXTRA_OEMAKE = " \
    'AOSP_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/aosp' \
    'EIGEN_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/eigen' \
    'GEMMLOWP_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/tensorflow/lite/tools/make/downloads/gemmlowp/' \
    'LIBTEXTCLASSIFIER_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/libtextclassifier/' \
    'ARMNN_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/armnn/' \
    'ARMNN_UTILS_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/armnnUtils/' \
    'SYSROOT=${STAGING_DIR_TARGET}' \
"

do_install() {
    oe_runmake install DESTDIR=${D} LIBDIR=${libdir} INCLUDEDIR=${includedir}
}
