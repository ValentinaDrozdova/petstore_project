# PetStore API

A REST API for managing pet records (dogs and cats), developed using Python, Django, and PostgreSQL.

API functions:

* Viewing a list of pets with filtering and pagination options.
* Adding new pets.
* Bulk deletion of pets by a list of identifiers, including associated photos.
* Uploading photos for a pet.
* API key authentication.

## Requirements

* Python 3.8+
* PostgreSQL Database
* Git

## Installation and Setup

1.  **Clone the repository:**
    ```bash
    git clone git@github.com:ValentinaDrozdova/petstore_project.git
    cd petstore_project
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Ensure `requirements.txt` includes `Django`, `djangorestframework`, `psycopg2-binary`, `Pillow`, etc.)*

4.  **Configure PostgreSQL Database:**
    * Create a PostgreSQL database (e.g., `petstore_db`).
    * Create a database user with a password and grant privileges on the created database.
    * Update the database connection settings in `petstore/settings.py` (the `DATABASES` section) with your database name, user, password, host, and port.

5.  **Configure API Key:**
    * Set your secret API key in `petstore/settings.py` by assigning a secure string to the `API_KEY` variable.
        **Note:** For production environments, it is strongly recommended to load the API key from environment variables or a secrets management system instead of hardcoding it in `settings.py`.

6.  **Apply database migrations:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

7.  **(Optional) Create a superuser for Django Admin:**
    ```bash
    python manage.py createsuperuser
    ```

## Running the Development Server

Execute the following command to start the Django development server:

```bash
python manage.py runserver
```

## Available API Endpoints

The API provides the following endpoints. All requests require the `X-API-KEY` header with your secret API key for authentication.

* **`GET /pets/`**
    * Retrieve a list of all pets.
    * Supports pagination using `limit` and `offset` query parameters.
    * Supports filtering by `has_photos=true` or `has_photos=false` query parameter.

* **`POST /pets/`**
    * Create a new pet.
    * Accepts pet data (e.g., `name`, `age`, `type`) in the request body (JSON).

* **`DELETE /pets/`**
    * Bulk delete pets.
    * Accepts a list of pet IDs (`ids`) in the request body (JSON).
    * Example request body: `{"ids": ["uuid1", "uuid2", ...]}`.
    * Upon successful deletion, the pet and all associated photos and their files will be removed.

* **`POST /pets/{id}/photo/`**
    * Upload a photo for the pet with the specified UUID.
    * Accepts the photo file in the request body using `multipart/form-data` with the field name `file`.

---

## Authentication

The API uses API key authentication. For successful requests, you must include the `X-API-KEY` header with the value of your secret key (set in `settings.py`) in each request.

Example using `curl`:

```bash
curl -X GET [http://127.0.0.1:8000/pets/](http://127.0.0.1:8000/pets/) -H "X-API-KEY: your_very_secret_API_key_for_tests"
```

## Tests

```bash
python manage.py test
```