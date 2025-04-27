# Quickstart

## Development

To get started with development of this project, clone the repository from GitHub:

```sh [git]
git clone https://github.com/twangodev/uw-coursemap.git
```

Next, create a `.env` file in the root directory of the project. This project contains an `.env.example` file that **works out of the box**. You can copy it to create your own `.env` file, or modify it to suit your needs.

```sh [sh]
cp .env.example .env
```

::: details .env.example
<<< @/../.env.example{dotenv}
:::

Next, determine whether you want to run the frontend, search, generation, or all. If you're not sure what you want to run, you should read [architecture](../concepts/architecture.md) to get a better understanding of the project. 

Frontend is the easiest to get started with, so we recommend starting there.

### Frontend

To begin development on the frontend, ensure you have [Node.js](https://nodejs.org/en/download/) installed. Then, navigate into the project directory and install the dependencies:

```sh [npm]
npm install
```

Next, start the development server:

```sh [npm]
npm run dev
```

You can now access the application with your browser at the specified URL.

> [!TIP]
> To preview the documentation run 
> ```sh [npm]
> npm run docs:dev
> ``` 

### Search
The search is a little more tricky to set up, as it uses [Pipenv] and [Elasticsearch].

First, you will need to initialize the [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) if you have
not done so already.

```sh [git]
git submodule update --init --recursive
```

#### Setup Elasticsearch

Next, you will need to install [Elasticsearch] on your machine. We recommend using [Docker] to run Elasticsearch, as it is the easiest way to get started. If you don't have Docker installed, you can follow the instructions on the [Docker website](https://docs.docker.com/get-docker/).

```sh [docker]
docker compose up -d
```

At this point, you will need to reconfigure your `.env` file to point to the Elasticsearch instance. As specified in the `docker-compose.yml`, the Docker container will run on `localhost:9200`, so you can use the following configuration for your `.env` file:

```dotenv
ELASTIC_HOST=https://localhost:9200
```

::: details docker-compose.yml
<<< @/../docker-compose.yml{yaml}
:::

#### Setup Flask

Finally, ensure you have [Python](https://www.python.org/downloads/) installed. Install [Pipenv] with the following command:

```sh [pip]
pip install pipenv --user
```

Next, navigate into the `search` directory and install the dependencies:

```sh [pipenv]
pipenv install
```

And now you can run the search server:

```sh [pipenv]
pipenv run python app.py
```

> [!TIP] 
> The search server requires the same environment variables as specified in the `.env` file in the root directory. See [Pipenv Shell](https://pipenv.pypa.io/en/latest/shell.html) for how to bring them into the shell.

PyCharm users, you can create a run configuration to run the search server with the environment variables from the `.env` file.
:::

### Generation

The generation process requires the same Python setup as the search. Install [Pipenv] and the dependencies as specified above. Then, navigate into the `generation` directory and run the following command:

```sh [pipenv]
pipenv run python main.py --help
```

For full details on how to run the generation process, see the [Generation](../codebase/generation.md) documentation.

## Deployment

We recommend deploying this application using [Docker] for ease of use. We publish both the frontend and search images to [Docker Hub] and the [GitHub Container Registry][GHCR], which `docker-compose.yml` will pull from by default.

To deploy the application, you will need to create a `.env` file in the root directory of the project, just like in [development](#development). You can use the `.env.example` file as a template and copy it to create your own `.env` file.

```sh [sh]
cp .env.example .env
```

> [!CAUTION]
> Ensure that you change `ELASTIC_PASSWORD` in the `.env` file to a secure password. This is the password for the `elastic` user in Elasticsearch, and it is used to authenticate the search server to Elasticsearch.

To run the application, run the following command:

```sh [docker]
docker compose up -d
```

This will start the application in detached mode. You can view the logs with the following command:

```sh [docker]
docker compose logs -f
```

To stop the application, run the following command:

```sh [docker]
docker compose down
```

To expose your application to the internet, you can use a production grade reverse proxy like [NGINX](https://www.nginx.com/), [Caddy](https://caddyserver.com/), or [Traefik](https://traefik.io/).

### Scaling

This application is designed to be horizontally scalable, meaning you can run multiple instances of the frontend and search servers to handle more traffic. 

Currently, there isn't enough demand to warrant horizontally scaling the application. However, if you would like to scale the application, you can use [Docker Swarm](https://docs.docker.com/engine/swarm/) or [Kubernetes](https://kubernetes.io/) to orchestrate the scaling process, or using an autoscaler group with your cloud provider of choice.

[docker]: https://www.docker.com/products/docker-desktop
[elasticsearch]: https://www.elastic.co/elasticsearch
[pipenv]: https://pipenv.pypa.io/en/latest/
[docker hub]: https://hub.docker.com/search?q=twango%2Fuw-coursemap
[GHCR]: https://github.com/twangodev?tab=packages&repo_name=uw-coursemap
