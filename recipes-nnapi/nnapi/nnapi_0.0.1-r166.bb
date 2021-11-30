require nnapi-0.0.1-r166.inc

DEPENDS = "nnapi-support tensorflow-lite nnapi-support openssl libtextclassifier virtual/libvendor-nn-hal gtest gmock"
RDEPENDS:${PN} = "nnapi-support libvendor-nn-hal"
RDEPENDS:${PN}-cts = "nnapi nnapi-support libtextclassifier "

SRC_URI += " \
    file://0002-nnapi-add-Makefiles.patch \
    file://0001-nnapi-optional-build-cts-of-nnapi.patch \
    file://0001-nnapi-add-missing-optional-include.patch \
    "

SRC_URI += "${@bb.utils.contains('PREFERRED_PROVIDER_virtual/libvendor-nn-hal', 'android-nn-driver', 'file://0001-nnapi-add-dummy-impl-of-validateRequestfor.patch', '', d)}"	

EXTRA_OEMAKE = " \
    'AOSP_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/aosp' \
    'EIGEN_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/eigen' \
    'GEMMLOWP_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/gemmlowp/' \
    'LIBTEXTCLASSIFIER_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/libtextclassifier/' \
    'ARMNN_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/armnn/' \
    'ARMNN_UTILS_INCLUDE=${STAGING_DIR_TARGET}/${includedir}/armnnUtils/' \
    'SYSROOT=${STAGING_DIR_TARGET}' \
    'LIBBASE=${STAGING_DIR_TARGET}/${libdir}/' \
    'BUILD_NNAPI_CTS=1' \
"

do_compile () {
    oe_runmake LIBDIR=${libdir} BINDIR=${bindir}
}

do_install() {
    oe_runmake install DESTDIR=${D} LIBDIR=${libdir} BINDIR=${bindir}
}

SOLIBS = ".so"
FILES_SOLIBSDEV = ""
FILES:${PN} += "${libdir}/* ${includedir} "

FILES:${PN}-cts = "${bindir}/nnapi-cts"
PACKAGES =+ "${PN}-cts"
