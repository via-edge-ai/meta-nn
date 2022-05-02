FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += " \
           file://0001-add-external-gpu-delegate.patch \
           file://0001-add-external-nnapi-delegate.patch \
           file://0001-tensorflow-lite-add-external-delegate.patch \
           file://0001-tflite-label_image.py-use-tflite-interpreter.patch \
"

DEPENDS += "virtual/libegl"

RDEPENDS:${PN} += " \
	python3-pillow \
"

TF_TARGET_EXTRA += " \
        tensorflow/lite/delegates/utils/nnapi_external_delegate:nnapi_external_delegate.so \
        tensorflow/lite/delegates/utils/gpu_external_delegate:gpu_external_delegate.so \
"

TF_ARGS_EXTRA += " \
         --copt -DCL_DELEGATE_NO_GL \
"

do_install:append() {
        # install external delegates
        install -d ${D}${libdir}
        install -m 644 ${S}/bazel-bin/tensorflow/lite/delegates/utils/gpu_external_delegate/gpu_external_delegate.so \
                ${D}${libdir}

        install -m 644 ${S}/bazel-bin/tensorflow/lite/delegates/utils/nnapi_external_delegate/nnapi_external_delegate.so \
                ${D}${libdir}

        #install python label_image script
        install -d ${D}${datadir}/label_image
        install -m 644 ${S}/tensorflow/lite/examples/python/label_image.py \
                ${D}${datadir}/label_image/

        #install headers
        cd "${S}/tensorflow/"
        for file in $(find . -name '*.h'); do
                install -d "${D}${includedir}/tensorflow/$(dirname -- "${file}")"
                install -m 0644 "${file}" "${D}${includedir}/tensorflow/${file}"
        done

        install -d ${D}${includedir}/eigen
        cp -r ${WORKDIR}/bazel/output_base/external/eigen_archive/Eigen ${D}/${includedir}/eigen/
        cp -r ${WORKDIR}/bazel/output_base/external/eigen_archive/unsupported ${D}/${includedir}/eigen/
        cp -r ${WORKDIR}/bazel/output_base/external/gemmlowp/ ${D}/${includedir}/
        cp -r ${S}//third_party/ ${D}/${includedir}

        install -d ${D}/${includedir}
        cd ${WORKDIR}/bazel/output_base/external/ruy/
        for file in $(find . -name '*.h'); do
                install -d "${D}${includedir}/$(dirname -- "${file}")"
                install -m 0644 "${file}" "${D}${includedir}/${file}"
        done
}

FILES:${PN} += "${libdir}"
INSANE_SKIP:${PN} += "dev-so \
                      already-stripped \
"

SOLIBS = ".so"
FILES_SOLIBSDEV = ""
ALLOW_EMPTY:${PN} = "1"
