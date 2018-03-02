FROM fedora:27
CMD ["pypi"]
ENTRYPOINT ["thoth-adviser"]
ENV \
 LANG=en_US.UTF-8 \
 THOTH_ADVISER_TMP_DIR='/tmp/thoth-adviser-install'

RUN \
 dnf update -y &&\
 mkdir -p ${THOTH_ADVISER_TMP_DIR}

# Install thoth-adviser itself
COPY ./ ${THOTH_ADVISER_TMP_DIR}
RUN \
 cd ${THOTH_ADVISER_TMP_DIR} &&\
 pip3 install . &&\
 cd / &&\
 rm -rf ${THOTH_ADVISER_TMP_DIR} &&\
 unset THOTH_ADVISER_TMP_DIR &&\
 dnf clean all
