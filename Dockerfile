FROM python:3.8
WORKDIR /var/app
VOLUME ["/var/app"]
RUN apt-get update \
&& apt-get install -y \
   cron \
&& touch /var/app/costbin.log \
&& rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN crontab -l | \
  { cat; echo "0 11 * * * /usr/local/bin/python3 /var/app/costbin.py --adsterra"; \
    cat; echo "5 11 * * * /usr/local/bin/python3 /var/app/costbin.py --propellerads"; \
    cat; echo "0 12 * * * /usr/local/bin/python3 /var/app/costbin.py --binom"; } | crontab -
CMD cron
