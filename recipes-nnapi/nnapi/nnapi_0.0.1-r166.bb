require nnapi-0.0.1-r166.inc

DEPENDS = "nnapi-support tensorflow-lite nnapi-support openssl libtextclassifier virtual/libvendor-nn-hal"
RDEPENDS:${PN} = "nnapi-support libvendor-nn-hal"

SRC_URI += " \
    file://0002-nnapi-add-Makefiles.patch \
    "
EXTRA_OEMAKE = " \
    'AOSP_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/aosp' \
    'EIGEN_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/eigen' \
    'GEMMLOWP_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/gemmlowp/' \
    'LIBTEXTCLASSIFIER_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/libtextclassifier/' \
    'ARMNN_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/armnn/' \
    'ARMNN_UTILS_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/armnnUtils/' \
    'SYSROOT=${STAGING_DIR_TARGET}' \
"

do_compile () {
    oe_runmake LIBDIR=${libdir}
}

do_install() {
    oe_runmake install DESTDIR=${D} LIBDIR=${libdir} INCLUDEDIR=${includedir}
}

SOLIBS = ".so"
FILES_SOLIBSDEV = ""
FILES:${PN} = "${libdir}/* ${includedir}"
