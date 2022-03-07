require xtensa-ann.inc

DEPENDS = " libapu nnapi-headers nnapi-support libsystem tensorflow-lite "
RDEPENDS:${PN} = " nnapi-support tensorflow-lite "

do_install:append() {
    install -d ${D}/${libdir}
    oe_soinstall ${WORKDIR}/prebuilts/common/yocto/libvendor-nn-hal.so.1.0 ${D}/${libdir}
}
