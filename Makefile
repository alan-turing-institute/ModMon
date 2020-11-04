DOCKERPORT=8888
HOSTPORT=8889
VERSION=0.0.2
CONTAINER=jannetta/modmon
NAME=modmon
DOCKERFILE=Dockerfile


echo:
	echo $(DOCKERFILE)
build:
	docker build --force-rm -f $(DOCKERFILE) -t $(CONTAINER):$(VERSION) .

run:
	docker run --rm -p 4567:4567 -p $(HOSTPORT):$(DOCKERPORT) -d -v modmon:/modmon/ --name $(NAME) $(CONTAINER):$(VERSION)

stop:
	docker stop $(NAME)

start:
	docker start $(NAME)

exec:
	docker exec -ti $(NAME) bash

tar:
	docker save -o $(NAME)$(VERSION).tar $(CONTAINER):$(VERSION)

install:
	docker load -i $(NAME)$(VERSION).tar

push:
	git push --atomic origin master $(VERSION)

network:
	docker network create --gateway 172.16.1.1 --subnet 172.16.1.0/24 mvc_network
