FROM python:3.5

RUN apt-get update && \
	apt-get -y install zip shellcheck jq curl

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

ENV TERRAFORM_VERSION=0.9.11
RUN wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -O /tmp/terraform.zip \
    && unzip /tmp/terraform.zip \
    && mv terraform /usr/bin/ \
    && rm /tmp/terraform.zip
RUN terraform version

RUN curl --silent https://releases.hashicorp.com/index.json | jq '{packer}' | egrep "linux_amd64" | sort -rh | head -1 | awk -F[\"] '{print $4}' > packer_version.txt
RUN wget -i packer_version.txt -O /tmp/packer.zip \
    && unzip /tmp/packer.zip \
    && mv packer /usr/bin/ \
    && rm /tmp/packer.zip
RUN packer version

COPY Gemfile* /
RUN apt-get install -y ruby \
    && gem install bundler \
    && bundle install
