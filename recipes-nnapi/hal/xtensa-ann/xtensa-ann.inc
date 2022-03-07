SUMMARY = "XtensaANN driver for the Android Neural Networks API"
DESCRIPTION = "Linux port of the XternsANN driver for NNAPI"
LICENSE = "CLOSED"

# Prebuilt binaries are available here: https://gitlab.com/mediatek/aiot/nda-cadence/prebuilts/

COMPATIBLE_MACHINE = "(i500-*|i350-*)"

PROVIDES = "virtual/libvendor-nn-hal"
RPROVIDES:${PN} = "libvendor-nn-hal"

SRCREV_FORMAT = "prebuilts"
SRCREV_prebuilts = "e9eee993dbbae68acb3c6454e2f1764de998020f"

SRC_URI = "git://gitlab.com/mediatek/aiot/nda-cadence/prebuilts.git;protocol=https;branch=main;destsuffix=prebuilts;name=prebuilts"

do_install() {
    install -d ${D}/${nonarch_base_libdir}
    install -d ${D}/${nonarch_base_libdir}/firmware

    case ${MACHINE} in
        i500-*)
             install -m 0644 ${WORKDIR}/prebuilts/i500/binaries/vp6/rproc-vp6-fw ${D}/${nonarch_base_libdir}/firmware
             ;;
        i350-*)
             install -m 0644 ${WORKDIR}/prebuilts/i350/binaries/vp6/rproc-vp6-fw ${D}/${nonarch_base_libdir}/firmware
             ;;
    esac
}

INSANE_SKIP:${PN} = "arch"
INSANE_SKIP:${PN} += " already-stripped"

FILES:${PN} += "${nonarch_base_libdir}/firmware/*"
