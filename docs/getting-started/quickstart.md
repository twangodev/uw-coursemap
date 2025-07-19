# Quickstart

## Development

To get started with development of this project, clone the repository from GitHub:

```sh [git]
git clone https://github.com/twangodev/uw-coursemap.git \
  --recurse-submodules
```

Next, create a `.env` file in the root directory of the project. This project contains an `.env.example`, which may be copied and modified for each environment.

```sh [sh]
cp .env.example .env
```

::: details .env.example
<<< @/../.env.example{dotenv}
:::

Next, determine whether you want to run the frontend, search, generation, or all. If you're not sure what you want to run, you should read up on the [architecture](architecture.md) to get a better understanding of the project.

Frontend is the easiest to get started with, so we recommend starting there.

### Frontend

To begin development on the frontend, ensure you have [Node.js](https://nodejs.org/en/download/) installed. Then, navigate into the project directory and install the dependencies:

```sh [npm]
npm install
```

You can now run the development server for the frontend, which should be accessible within your browser at the specified URL.

```sh [npm]
npm run dev
```

::: details How do I preview documentation?
We use [VitePress](https://vitepress.dev/) to generate the documentation for this project, as it runs alongside the frontend. To preview the documentation, you can run the following command:

```sh [npm]
npm run docs:dev
```

:::

### Search

First, you will need to initialize the [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) if you have
not done so already.

```sh [git]
git submodule update --init --recursive
```

#### Setup Elasticsearch

Next, you will need to install [Elasticsearch] on your machine. We recommend using [Docker] to run Elasticsearch, as it is the easiest way to get started. If you don't have Docker installed, it can be easily downloaded with [Docker Desktop][docker]

```sh [docker]
docker compose up -d
```

At this point, you will need to reconfigure your environment variables to point to the Elasticsearch instance. As specified in the `docker-compose.yml`, the Docker container binds to `localhost:9200`, so you can use the following configuration:

```dotenv
ELASTIC_HOST=https://localhost:9200
```

::: details docker-compose.yml
<<< @/../docker-compose.yml{yaml}
:::

> [!IMPORTANT]
> Ensure that your `DATA_DIR` environment variable is correctly configured. During local development, this should point to a directory on your local machine where the data will be stored. The default is `./data`.
>
> In Docker Compose, we mount the data directly onto the root directory of the container, so you can use `/data` as the value for `DATA_DIR`.

#### Setup Flask

Finally, ensure you have [Python](https://www.python.org/downloads/) installed. Follow the documentation to setup a virtual environment with [uv](https://docs.astral.sh/uv/getting-started/installation/)

Install the dependencies for the search service:

```sh [uv]
uv sync
```

We recommend running the service from the project root directory, as that is likely where your environment variables are set up. You can run the search service with the following command:

```sh [uv]
uv run python ./search/app.py
```

This spins up a development server that listens for requests.

> [!CAUTION]
> This server is not intended for production use. It is only meant for development and testing purposes. For production, you should use a WSGI server like [Gunicorn](https://gunicorn.org/), which is already configured through the `uw-coursemap-search` Docker image.

### Generation

The generation process requires the same Python setup as the search. Install [uv] and the dependencies as specified above, just in the `generation` directory.

> [!TIP]
> Ideally, you should create separate virtual environments for the search and generation processes.

```sh [uv]
uv run python ./generation/main.py --help
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

[frontend]: #frontend
[docker]: https://www.docker.com/products/docker-desktop
[elasticsearch]: https://www.elastic.co/elasticsearch
[uv]: https://docs.astral.sh/uv/
[docker hub]: https://hub.docker.com/search?q=twango%2Fuw-coursemap
[GHCR]: https://github.com/twangodev?tab=packages&repo_name=uw-coursemap
