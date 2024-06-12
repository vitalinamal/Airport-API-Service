# Airport API Service ✈️

## Overview 🔎

This project is a Django-based application that provides a REST API for managing flight and ticket information. The API
allows users to view, create, and manage flight bookings with proper authentication and permissions.

## Features 🐍

- User authentication and authorization
- Flight and ticket management
- Custom permissions for API endpoints
- Auto-generated API documentation using `drf-spectacular`
- Caching for optimized performance
- Dockerized for easy deployment
- JSON Web Token (JWT) authentication

## Project Structure 🐍⚙️

- `models.py`: Contains the database models for flights and tickets.
- `permissions.py`: Defines custom permission classes.
- `schemas.py`: Configures API documentation schemas.
- `serializers.py`: Serializes and deserializes data between JSON and model instances.
- `urls.py`: URL routing configuration.
- `views.py`: Viewsets and views for handling API requests.
- `user`: Contains user management functionalities.
- `Dockerfile`: Docker configuration for the application.
- `docker-compose.yml`: Docker Compose configuration for multi-container setup.

The project requires certain environment variables to be set. You can create a `.env` file in the root directory of your
project and add the following variables:

```env
POSTGRES_PASSWORD=your_database_password
POSTGRES_USER=your_database_user
POSTGRES_DB=your_database_name
POSTGRES_HOST=your_database_host
POSTGRES_PORT=your_database_port
SECRET_KEY=your_django_secret_key
```

## Installation 🔧

### Using Docker 🐳

- Ensure that Docker is installed on your system. You can download and install Docker from [here](https://www.docker.com/products/docker-desktop).


1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   
2. Build and start the containers:

   ```bash
   docker-compose up --build
   
3. Create a superuser inside the Docker container:
   
   ```bash
   docker-compose exec web python manage.py createsuperuser

4. Access the development server:

   - The server will be running at http://127.0.0.1:8001/

### Without Docker ⭐️

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   
2. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`

   
3. Install the dependencies:
   
   ```bash
   pip install -r requirements.txt

4. Apply the migrations:
   
   ``` bash
   python manage.py migrate

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   
6. Start the development server:
   ```bash
   python manage.py runserver


## Usage 🚀

### API Endpoints 📍

The API provides endpoints for 
 - Crew
 - Airplanes
 - Airplane Types
 - Airports
 - Routs
 - Flight
 - Orders

See an example below

- `GET /api/flights/`: List all flights.
- `POST /api/flights/`: Create a new flight.
- `GET /api/flights/{id}/`: Retrieve a specific flight.
- `PUT /api/flights/{id}/`: Update a specific flight.
- `DELETE /api/flights/{id}/`: Delete a specific flight.

### Permissions 🔐

- **IsAdminOrIfAuthenticatedReadOnly**: Allows read-only access for authenticated users and full access for admin users.

### API Documentation

Auto-generated API documentation is available at `/api/schema/` using `drf-spectacular`.

### Testing 📘

To run the tests:
   
   ```bash
   python manage.py test
   ```

## Contact 💌

For any inquiries, please contact [vitalinamalinovskaya557@gmail.com](mailto:vitalinamalinovskaya557@gmail.com).

