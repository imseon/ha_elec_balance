from python:3

RUN apt update && apt install -y chromium nginx ttf-wqy-microhei

RUN cd /tmp && \
    wget https://chromedriver.storage.googleapis.com/101.0.4951.41/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/bin/ && rm -f chromedriver_linux64.zip && \
    touch /var/log/elec_balance.log

WORKDIR /elec_balance
RUN pip3 install selenium pillow requests
RUN echo '#!/bin/bash\n\
python3 /elec_balance/fetch.py 1>>/var/log/elec_balance.log 2>/dev/null\n\
cat /elec_balance/balance' > /elec_balance/fetch && chmod +x /elec_balance/fetch

COPY custom_components/elec_balance /elec_balance
COPY entrypoint /entrypoint

CMD ["bash", "/entrypoint"]