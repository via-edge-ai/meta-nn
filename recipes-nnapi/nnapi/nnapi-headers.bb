# only install nnapi header files

require nnapi-0.0.1-r166.inc

do_install() {
    mkdir -p ${D}/${includedir}
    mkdir -p ${D}/${includedir}/nnapi
    cd ${S}
    find nn -name '*.h' -exec cp --parents "{}" ${D}/${includedir}/nnapi/ \;
}
