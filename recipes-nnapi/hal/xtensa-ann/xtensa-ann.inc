SUMMARY = "XtensaANN driver for the Android Neural Networks API"
DESCRIPTION = "Linux port of the XternsANN driver for NNAPI"
LICENSE = "CLOSED"

inherit features_check

REQUIRED_DISTRO_FEATURES = "nda-mtk"

# Prebuilt binaries are available here: https://gitlab.com/mediatek/aiot/nda-cadence/prebuilts/

COMPATIBLE_MACHINE = "(i500-*|i350-*)"

PROVIDES = "virtual/libvendor-nn-hal"
RPROVIDES:${PN} = "libvendor-nn-hal"

SRCREV_FORMAT = "prebuilts"
SRCREV_prebuilts = "f9415597b98788f48ba8b86b56d070a3f833e636"

SRC_URI = "git://git@gitlab.com/mediatek/aiot/nda-cadence/prebuilts.git;protocol=ssh;branch=main;destsuffix=prebuilts;name=prebuilts"

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
