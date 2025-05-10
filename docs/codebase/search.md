# Search

A search engine for courses, instructors, and departments at the University of Wisconsin-Madison, powered by [Elasticsearch](https://www.elastic.co/).

The dataset used for this project is from [generation](../generation). The dataset is then indexed into Elasticsearch for searching.

## Usage

### Prerequisites

For a single instance of Elasticsearch, you can run it using Docker. We've included a `docker-compose.yml` file in the root of this project that will start an Elasticsearch instance for you.

```bash
docker-compose up -d
```

The elastic search instance is now exposed on `localhost:9200`. Within both production and development environments, elasticsearch is not meant to be accessed directly. Instead, Flask sits in front of Elasticsearch and handles all requests.

To run the Flask server, you can use the following commands (assuming you have `pipenv` installed):

```bash
pipenv sync
```

Change directories back to the project root directory, and now you can run the search server:

```sh [pipenv]
pipenv run python ./search/app.py
```

We will eventually configure WSGI to run the Flask server in production.

### API

The API is a simple RESTful API that allows you to search for courses, instructors, and departments.

#### `POST /search`

This endpoint allows you to search for courses, instructors, and departments. The request body should be a JSON object with the following keys:

- `query`: The search query

Example request:

```json
{
  "query": "computer science"
}
```

The response will be a JSON object with the

- `courses`: A list of courses that match the query
    - `course_id`: The course ID. This is compatible with the `GET /courses` endpoint in primary data API, from generation.
    - `course_title`: The course title
    - `course_number`: The course number (integer)
    - `subjects`: A list of departments that the course belongs to. Note that this is the shorthand department code, not the full department name.
    - `department`: The full department names that the course belongs to
- `instructors`: A list of instructors that match the query
    - `instructor_id`: The instructor ID. This is compatible with the `GET /instructors` endpoint in the primary data API, from generation.
    - `name`: The instructor's name
    - `official_name`: The instructor's official name. Just name with extra formatting.
    - `email`: The instructor's email
    - `position`: The instructor's position
    - `department`: The instructor's department
- `subjects`: A list of departments that match the query
    - `subject_id`: The department ID. This is just the shorthand department code.
    - `name`: The department's full name