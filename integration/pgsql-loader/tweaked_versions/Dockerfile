FROM python:3.8
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt && \
	chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["loader"]
