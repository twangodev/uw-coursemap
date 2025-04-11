SVELTE_IMAGE ?= twangodev/uw-coursemap/svelte
FLASK_IMAGE ?= twangodev/uw-coursemap/search
TAG ?= latest

.PHONY: build-svelte build-flask push-svelte push-flask

build-svelte:
	docker build -f Dockerfile -t $(SVELTE_IMAGE):$(TAG) .

build-flask:
	docker build -f search/Dockerfile -t $(FLASK_IMAGE):$(TAG) ./search

push-svelte:
	docker push $(SVELTE_IMAGE):$(TAG)

push-flask:
	docker push $(FLASK_IMAGE):$(TAG)