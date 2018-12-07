FROM	rocker/shiny@sha256:627a2b7b3b6b1f6e33d37bdba835bbbd854acf70d74010645af71fc3ff6c32b6
ENV	DEBIAN_FRONTEND	noninteractive
WORKDIR	/home/app
ADD	requirements.txt	/home/app
RUN	apt-get update -y \
	&& apt-get upgrade -y \
	&& apt-get install -y \
	python3.7 \
	python3.7-dev \
	python3-pip \
	libxml2-dev \
	libssl-dev \
	gfortran-8-x86-64-linux-gnux32 \
	libbz2-dev \
	libudunits2-dev
RUN	python3.7 -m pip install -r requirements.txt
RUN	install2.r devtools Rcpp
RUN	apt-get clean \
	&& rm -rf /var/lib/apt/lists/
ADD	.	/home/app
EXPOSE	8000
CMD	["python3.7","server.py"]
