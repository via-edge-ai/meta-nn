require xtensa-ann.inc

DEPENDS = " \
    ${@bb.utils.contains('TFLITE_PREBUILT', '1', 'tesorflowlite-prebuilt', 'tensorflow-lite', d)} \
    libapu \
    nnapi-headers \
    nnapi-support \
    libsystem \
"

RDEPENDS:${PN} = " \
    nnapi-support \
    ${@bb.utils.contains('TFLITE_PREBUILT', '1', 'tesorflowlite-prebuilt', 'tensorflow-lite', d)} \
"  

do_install:append() {
    install -d ${D}/${libdir}
    oe_soinstall ${WORKDIR}/prebuilts/common/yocto/libvendor-nn-hal.so.1.0 ${D}/${libdir}
}
