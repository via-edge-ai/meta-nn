require  recipes-framework/tensorflow/tensorflow.inc

FILESEXTRAPATHS_prepend = "${THISDIR}/../../../meta-tensorflow/recipes-framework/tensorflow/files/:"

SRC_URI += " \
           file://0001-add-yocto-toolchain-to-support-cross-compiling.patch \
           file://0001-fix-build-tensorflow-lite-examples-label_image-label.patch \
           file://0001-label_image-tweak-default-model-location.patch \
           file://0001-label_image.lite-tweak-default-model-location.patch \
           file://0001-CheckFeatureOrDie-use-warning-to-avoid-die.patch \
           file://0001-support-32-bit-x64-and-arm-for-yocto.patch \
           file://BUILD.in \
           file://BUILD.yocto_compiler \
           file://cc_config.bzl.tpl \
           file://yocto_compiler_configure.bzl \
           file://0001-add-external-gpu-delegate.patch \
           file://0001-Add-support-of-bazel-args.patch \
           file://grace_hopper.jpg \
           file://label_image.py \
           file://labels.txt \
           file://mobilenet_v2_1.0_224.tflite \
           file://mobilenet_v2_1.0_224_quant.tflite \
          "

DEPENDS += " virtual/opencl "
RDEPENDS_${PN} += " \
    python3 \
    python3-pip \
    python3-pillow \
    libatomic \
    opencl \
"

export PYTHON_BIN_PATH="${PYTHON}"
export PYTHON_LIB_PATH="${STAGING_LIBDIR_NATIVE}/${PYTHON_DIR}/site-packages"

export CROSSTOOL_PYTHON_INCLUDE_PATH="${STAGING_INCDIR}/python${PYTHON_BASEVERSION}${PYTHON_ABI}"

do_configure_append () {
    if [ ! -e ${CROSSTOOL_PYTHON_INCLUDE_PATH}/pyconfig-target.h ];then
        mv ${CROSSTOOL_PYTHON_INCLUDE_PATH}/pyconfig.h ${CROSSTOOL_PYTHON_INCLUDE_PATH}/pyconfig-target.h
    fi

    install -m 644 ${STAGING_INCDIR_NATIVE}/python${PYTHON_BASEVERSION}${PYTHON_ABI}/pyconfig.h \
       ${CROSSTOOL_PYTHON_INCLUDE_PATH}/pyconfig-native.h

    cat > ${CROSSTOOL_PYTHON_INCLUDE_PATH}/pyconfig.h <<ENDOF
#if defined (_PYTHON_INCLUDE_TARGET)
#include "pyconfig-target.h"
#elif defined (_PYTHON_INCLUDE_NATIVE)
#include "pyconfig-native.h"
#else
#error "_PYTHON_INCLUDE_TARGET or _PYTHON_INCLUDE_NATIVE is not defined"
#endif // End of #if defined (_PYTHON_INCLUDE_TARGET)

ENDOF

    mkdir -p ${S}/third_party/toolchains/yocto/
    sed "s#%%CPU%%#${BAZEL_TARGET_CPU}#g" ${WORKDIR}/BUILD.in  > ${S}/third_party/toolchains/yocto/BUILD
    chmod 644 ${S}/third_party/toolchains/yocto/BUILD
    install -m 644 ${WORKDIR}/cc_config.bzl.tpl ${S}/third_party/toolchains/yocto/
    install -m 644 ${WORKDIR}/yocto_compiler_configure.bzl ${S}/third_party/toolchains/yocto/
    install -m 644 ${WORKDIR}/BUILD.yocto_compiler ${S}

    CT_NAME=$(echo ${HOST_PREFIX} | rev | cut -c 2- | rev)
    SED_COMMAND="s#%%CT_NAME%%#${CT_NAME}#g"
    SED_COMMAND="${SED_COMMAND}; s#%%WORKDIR%%#${WORKDIR}#g"
    SED_COMMAND="${SED_COMMAND}; s#%%YOCTO_COMPILER_PATH%%#${BAZEL_OUTPUTBASE_DIR}/external/yocto_compiler#g"

    sed -i "${SED_COMMAND}" ${S}/BUILD.yocto_compiler \
                            ${S}/WORKSPACE

    ${TF_CONFIG} \
    ./configure
}

TF_TARGET_EXTRA ??= ""

export CUSTOM_BAZEL_FLAGS = " \
    ${TF_ARGS_EXTRA} \
    --jobs=auto \
    -c opt \
    --cpu=${BAZEL_TARGET_CPU} \
    --crosstool_top=@local_config_yocto_compiler//:toolchain \
    --host_crosstool_top=@bazel_tools//tools/cpp:toolchain \
"

do_compile () {
    export CT_NAME=$(echo ${HOST_PREFIX} | rev | cut -c 2- | rev)
        export CROSSTOOL_PYTHON_INCLUDE_PATH="${STAGING_INCDIR}/python${PYTHON_BASEVERSION}${PYTHON_ABI}"
    unset CC

    # build tensorflowlite, external gpu/nanpi delegate and benchmark_model
    ${BAZEL} build \
        ${CUSTOM_BAZEL_FLAGS} \
        --copt -DTF_LITE_DISABLE_X86_NEON --copt -DCL_DELEGATE_NO_GL --copt -DMESA_EGL_NO_X11_HEADERS \
        //tensorflow/lite/tools/benchmark:benchmark_model \
        //tensorflow/lite/delegates/utils/gpu_external_delegate:gpu_external_delegate.so \
        //tensorflow/lite:libtensorflowlite.so

    # build pip package
    ${S}/tensorflow/lite/tools/pip_package/build_pip_package_with_bazel.sh
}

do_install() {
    #install libs
    install -d ${D}${libdir}
    install -m 644 ${S}/bazel-bin/tensorflow/lite/libtensorflowlite.so \
        ${D}${libdir}

    install -m 644 ${S}/bazel-bin/tensorflow/lite/delegates/utils/gpu_external_delegate/gpu_external_delegate.so \
        ${D}${libdir}

    #install benchmark_model binary
    install -d ${D}${bindir}
    install -m 755 ${S}/bazel-bin/tensorflow/lite/tools/benchmark/benchmark_model \
        ${D}${bindir}

    #install pip package
    install -d ${D}/${PYTHON_SITEPACKAGES_DIR}
    ${STAGING_BINDIR_NATIVE}/pip3 install --disable-pip-version-check -v \
        -t ${D}/${PYTHON_SITEPACKAGES_DIR} --no-cache-dir --no-deps \
        ${S}/tensorflow/lite/tools/pip_package/gen/tflite_pip/python3/dist/tflite_runtime-${PV}-*.whl

    #install headers
    cd "${S}/tensorflow/"
    for file in $(find . -name '*.h'); do
        install -d "${D}${includedir}/tensorflow/$(dirname -- "${file}")"
        install -m 0644 "${file}" "${D}${includedir}/tensorflow/${file}"
    done

    cp -r ${WORKDIR}/bazel/output_base/external/eigen_archive/ ${D}/${includedir}/eigen
    cp -r ${WORKDIR}/bazel/output_base/external/gemmlowp/ ${D}/${includedir}/
    cp -r ${S}//third_party/ ${D}/${includedir}

    install -d ${D}/${includedir}
    cd ${WORKDIR}/bazel/output_base/external/ruy/
    for file in $(find . -name '*.h'); do
        install -d "${D}${includedir}/$(dirname -- "${file}")"
        install -m 0644 "${file}" "${D}${includedir}/${file}"
    done

    install -d ${D}/home/
    install -d ${D}/home/root
    install -d ${D}/home/root/label_image
    install -m 0644 ${WORKDIR}/grace_hopper.jpg ${D}/home/root/label_image/
    install -m 0644 ${WORKDIR}/labels.txt ${D}/home/root/label_image/
    install -m 0644 ${WORKDIR}/label_image.py ${D}/home/root/label_image/
    install -m 0644 ${WORKDIR}/*.tflite ${D}/home/root/label_image/
}

INSANE_SKIP_${PN} += "dev-so \
                      already-stripped \
                     "

SOLIBS = ".so"
FILES_SOLIBSDEV = ""
ALLOW_EMPTY_${PN} = "1"

FILES_${PN} += "${libdir} /home/root/*"

inherit siteinfo unsupportarch
python __anonymous() {
    if d.getVar("SITEINFO_ENDIANNESS") == 'be':
        msg =  "\nIt failed to use pre-build model to do predict/inference on big-endian platform"
        msg += "\n(such as qemumips), since upstream does not support big-endian very well."
        msg += "\nDetails: https://github.com/tensorflow/tensorflow/issues/16364"
        bb.warn(msg)
}
