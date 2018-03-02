FROM fedora:27
CMD ["pypi"]
ENTRYPOINT ["thoth-advisor"]
ENV \
 LANG=en_US.UTF-8 \
 THOTH_ADVISOR_TMP_DIR='/tmp/thoth-advisor-install'

RUN \
 dnf update -y &&\
 mkdir -p ${THOTH_ADVISOR_TMP_DIR}

# Install thoth-advisor itself
COPY ./ ${THOTH_ADVISOR_TMP_DIR}
RUN \
 cd ${THOTH_ADVISOR_TMP_DIR} &&\
 python3 setup.py install &&\
 cd / &&\
 rm -rf ${THOTH_ADVISOR_TMP_DIR} &&\
 unset THOTH_ADVISOR_TMP_DIR &&\
 dnf clean all &&\
