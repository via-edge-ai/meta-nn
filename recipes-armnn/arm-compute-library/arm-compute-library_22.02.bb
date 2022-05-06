SUMMARY = "The ARM Computer Vision and Machine Learning library"
DESCRIPTION = "The ARM Computer Vision and Machine Learning library is a set of functions optimised for both ARM CPUs and GPUs."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=f3c5879801d3cffc4ac2399f2b8e8ec5"

inherit scons

#recipe based on https://github.com/Witekio/meta-machinelearning/blob/master/recipes-arm/arm-compute-library/arm-compute-library_19.02.bb

SRC_URI = "git://github.com/ARM-software/ComputeLibrary.git;protocol=https;branch=master;name=arm-compute-library \
           file://0001-enable-yocto-build.patch \
           file://0001-Remove-unknown-variables-treated-as-error.patch \
           "

SRCREV = "8f587de9214dbc3aee4ff4eeb2ede66747769b19"

EXTRA_OESCONS:aarch64 = "arch=arm64-v8a extra_cxx_flags="-fPIC" Werror=0 asserts=0 debug=0 benchmark_tests=0 validation_tests=0 embed_kernels=1 openmp=1 opencl=1 neon=1 opencl=1 set_soname=1"

S = "${WORKDIR}/git"

LIBS += "-larmpl_lp64_mp"

do_install() {
    CP_ARGS="-Prf --preserve=mode,timestamps --no-preserve=ownership"

    install -d ${D}${libdir}
    for lib in ${S}/build/*.so*
    do
        cp $CP_ARGS $lib ${D}${libdir}
    done

    # Install 'example' and benchmark executables
    install -d ${D}${bindir}
    find ${S}/build/examples/ -maxdepth 1 -type f -executable -exec cp $CP_ARGS {} ${D}${bindir} \;
    #cp $CP_ARGS ${S}/build/tests/arm_compute_benchmark ${D}${bindir}

    # Install built source package as expected by ARMNN
    install -d ${D}${includedir}
    cp $CP_ARGS ${S}/arm_compute ${D}${includedir}/
    cp $CP_ARGS ${S}/support ${D}${includedir}/
    install -d ${D}${includedir}
    cp $CP_ARGS ${S}/include/half ${D}${includedir}/.

    install -d ${D}${includedir}/src/core
    cp $CP_ARGS ${S}/src/core/CL ${D}${includedir}/src/core
}

INSANE_SKIP:${PN} = "ldflags"
INSANE_SKIP:${PN}-dev = "dev-elf ldflags"

FILES:${PN}-source = "${datadir}/${BPN}"
INSANE_SKIP:${PN}-source = "ldflags libdir staticdev"
INHIBIT_PACKAGE_DEBUG_SPLIT = "1"

