FROM python:3

RUN pip install --no-cache-dir gitlab-registry-usage

ENTRYPOINT ["gitlab-registry-usage"]
CMD ["-h"]
