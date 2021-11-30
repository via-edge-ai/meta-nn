FILESEXTRAPATHS_prepend := "${THISDIR}/files:"

TOOLCHAIN = "clang"

SRC_URI += " \
        file://0001-config-compiler.patch \
       "