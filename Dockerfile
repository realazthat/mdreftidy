FROM python:3.12-slim


WORKDIR /mdreftidy

# apt-get -y --no-install-recommends install git=1:2.39.2-1.1 &&
# apt-get -y upgrade &&

RUN apt-get -y update && apt-get -y --no-install-recommends install bash && \
  apt-get -y clean && \
  apt-get -y autoremove && \
  rm -rf /var/lib/apt/lists/* && \
  useradd -m -d /home/user -s /bin/bash user && \
  pip install --no-cache-dir --upgrade pip setuptools wheel && \
  mkdir -p /home/user/.local && \
  chown -R user:user /mdreftidy /home/user/.local && \
  chmod -R a+wrX /mdreftidy

COPY --chown=user:user . /mdreftidy

USER user
WORKDIR /mdreftidy
ENV PATH=/home/user/.local/bin:$PATH
ENV PYTHONPATH=/home/user/.local/lib/python3.12/site-packages
RUN pip install --no-cache-dir --prefix=/home/user/.local .

# This is where the user will mount their data to.
WORKDIR /data

ENTRYPOINT ["python", "-m", "mdreftidy.cli"]
CMD ["--help"]
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -m mdreftidy.cli --version || exit 1
