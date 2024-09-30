# ZapTalk

## Project goals
This project provides a Django Rest Framework API for the [ZapTalk React web app](https://github.com/PetterJohanssonTilia/zaptalk_frontend).

Zaptalk is designed to be a a community driven app for old movie enthusiasts with the mains goals being:
1. Deliver a User-Friendly Experience: The app aims to provide an intuitive and accessible user interface that allows users to easily explore old movies, interact with profiles, and enjoy a seamless browsing experience.
2. Implement Key Social Features: Provide functionality for users to create and manage profiles, like movies, follow other profiles, and generate a personalized movie feed based on their interests and interactions.
3. Focus on Minimum Viable Product (MVP): Prioritize essential features, ensuring timely delivery of core functionalities like movie lookup, likes, follows, and user feed within the project's timeframe, while leaving room for future enhancements.

## Table of contents
- [TribeHub](#tribehub)
  * [Project goals](#project-goals)
  * [Table of contents](#table-of-contents)
  * [Planning](#planning)
    + [Data models](#data-models)
      - [**Profile**](#--profile--)
      - [**Tribe**](#--tribe--)
      - [**Event**](#--event--)
    + [**Notification**](#--notification--)
    + [**Contact**](#--contact--)
  * [API endpoints](#api-endpoints)
  * [Frameworks, libraries and dependencies](#frameworks--libraries-and-dependencies)
    + [django-cloudinary-storage](#django-cloudinary-storage)
    + [dj-allauth](#dj-allauth)
    + [dj-rest-auth](#dj-rest-auth)
    + [djangorestframework-simplejwt](#djangorestframework-simplejwt)
    + [dj-database-url](#dj-database-url)
    + [psychopg2](#psychopg2)
    + [python-dateutil](#python-dateutil)
    + [django-recurrence](#django-recurrence)
    + [django-filter](#django-filter)
    + [django-cors-headers](#django-cors-headers)
  * [Testing](#testing)
    + [Manual testing](#manual-testing)
    + [Automated tests](#automated-tests)
    + [Python validation](#python-validation)
    + [Resolved bugs](#resolved-bugs)
      - [Bugs found while testing the API in isolation](#bugs-found-while-testing-the-api-in-isolation)
      - [Bugs found while testing the React front-end](#bugs-found-while-testing-the-react-front-end)
    + [Unresolved bugs](#unresolved-bugs)
  * [Deployment](#deployment)
  * [Credits](#credits)


## Planning
Planning started by creating user stories for the frontend application and labaling them with importance and size. The user stories were used to inform wireframes mapping out the intended functionality and 'flow' through the app.
With the user stories in mind I began creating the models for the API endpoints.

### Data models
Data model schema were planned in parallel with the API endpoints, using an entity relationship diagram.

Custom models implemented for ZapTalk are:

# ZapTalk Models Documentation

## Like Model

| Field | Type | Description |
| --- | --- | --- |
| user | ForeignKey | Reference to User model |
| content_type | ForeignKey | Reference to ContentType for generic relations |
| object_id | PositiveIntegerField | ID of the liked object |
| content_object | GenericForeignKey | Reference to the liked object |
| created_at | DateTimeField | When the like was created |

The `Like` model uses a generic relation, allowing it to be associated with different types of content (e.g., movies, comments). It has a unique constraint to prevent duplicate likes.

## Movie Model

| Field | Type | Description |
| --- | --- | --- |
| title | CharField | Movie title |
| year | IntegerField | Release year |
| cast | JSONField | Cast information |
| genres | JSONField | Genre information |
| href | CharField | Related URL (optional) |
| extract | TextField | Movie description |
| thumbnail | URLField | Movie poster image URL |
| thumbnail_width | IntegerField | Thumbnail width |
| thumbnail_height | IntegerField | Thumbnail height |
| likes | GenericRelation | Relation to Like model |

The `Movie` model includes methods to get the default content type for likes and properties to count likes and comments.

## UserProfile Model

| Field | Type | Description |
| --- | --- | --- |
| user | OneToOneField | Reference to User model |
| avatar | CloudinaryField | User profile picture |
| bio | TextField | User biography |
| location | CharField | User location |
| birth_date | DateField | User's birth date |
| website | URLField | User's website |
| followers | ManyToManyField | Self-referential field for user followers |

The `UserProfile` model includes methods to get comment count, total likes received, follower/following counts, and to check if a user is following another or is banned.

## Comment Model

| Field | Type | Description |
| --- | --- | --- |
| user | ForeignKey | Reference to User model |
| movie | ForeignKey | Reference to Movie model |
| content | TextField | Comment content |
| created_at | DateTimeField | When the comment was created |
| updated_at | DateTimeField | When the comment was last updated |
| likes | GenericRelation | Relation to Like model |

The `Commnet` model includes methods to get commentor, number of likes, update/create at and what movie the comment refers to.

## Ban Model

| Field | Type | Description |
| --- | --- | --- |
| user | ForeignKey | Reference to banned User |
| banned_by | ForeignKey | Reference to User who issued the ban |
| reason | TextField | Ban reason |
| banned_at | DateTimeField | When the ban was issued |
| expires_at | DateTimeField | Ban expiration (optional) |
| is_active | BooleanField | Indicates if the ban is currently active |

The `Ban` Model represents bans in the system, it allows staff to ban users. it includes information about the reason of the ban, banned by, and banned at

## BanAppeal Model

| Field | Type | Description |
| --- | --- | --- |
| ban | ForeignKey | Reference to Ban model |
| content | TextField | Appeal content |
| created_at | DateTimeField | When the appeal was created |
| is_resolved | BooleanField | Indicates if the appeal has been resolved |
| is_approved | BooleanField | Indicates if the appeal was approved |
| reviewed_by | ForeignKey | Reference to User who reviewed the appeal |
| reviewed_at | DateTimeField | When the appeal was reviewed |

The ``BanAppeal` model is used for a banned user to create a ban appeal, It also allows for the staff to review and unban that user.

## Notification Model

| Field | Type | Description |
| --- | --- | --- |
| recipient | ForeignKey | Reference to User receiving the notification |
| sender | ForeignKey | Reference to User triggering the notification |
| notification_type | CharField | Type of notification ('follow', 'like') |
| is_read | BooleanField | Indicates if the notification has been read |
| created_at | DateTimeField | When the notification was created |

The `Notification` model is used to see who gets a notification, who triggers the notification and what type of notification, if it's from a like or a comment


# API endpoints

## Root and Authentication Endpoints

| Endpoint | Description | Method | CRUD | View Type |
|----------|-------------|--------|------|-----------|
| `/api/` | API root providing links to main resources | GET | Read | List |
| `/api/token/` | Obtain JWT token pair | POST | Create | N/A |
| `/api/token/refresh/` | Refresh JWT token | POST | Create | N/A |
| `/api-auth/` | DRF authentication views | Various | Various | Various |
| `/api/auth/registration/` | User registration | POST | Create | N/A |

## Resource Endpoints

| Endpoint | Description | Methods | CRUD | View Type |
|----------|-------------|---------|------|-----------|
| `/api/movies/` | List or create movies | GET, POST | Read, Create | List |
| `/api/movies/<id>/` | Retrieve, update or delete a movie | GET, PUT, PATCH, DELETE | Read, Update, Delete | Detail |
| `/api/movies/<id>/random/` | Get a random movie | GET | Read | Detail |
| `/api/profiles/` | List or create user profiles | GET, POST | Read, Create | List |
| `/api/profiles/<id>/` | Retrieve, update or delete a user profile | GET, PUT, PATCH, DELETE | Read, Update, Delete | Detail |
| `/api/profiles/me/` | Get or update the current user's profile | GET, PUT, DELETE | Read, Update, Delete | Detail |
| `/api/profiles/<id>/follow/` | Follow or unfollow a user | POST | Create/Delete | Detail |
| `/api/profiles/<id>/followers/` | Get a user's followers | GET | Read | List |
| `/api/profiles/<id>/following/` | Get users a user is following | GET | Read | List |
| `/api/profiles/<id>/following_list/` | Get a detailed list of users a user is following | GET | Read | List |
| `/api/profiles/<id>/likes/` | Get a user's likes | GET | Read | List |
| `/api/profiles/<id>/is_banned/` | Check if a user is banned | GET | Read | Detail |
| `/api/likes/` | List all likes | GET, POST | Read, Create | List |
| `/api/likes/<id>/` | Retrieve, update or delete a like | GET, PUT, PATCH, DELETE | Read, Update, Delete | Detail |
| `/api/likes/toggle_like/` | Toggle like on a movie or comment | POST | Create/Delete | Detail |
| `/api/comments/` | List or create comments | GET, POST | Read, Create | List |
| `/api/comments/<id>/` | Retrieve, update or delete a comment | GET, PUT, PATCH, DELETE | Read, Update, Delete | Detail |
| `/api/bans/` | List or create bans | GET, POST | Read, Create | List |
| `/api/bans/<id>/` | Retrieve, update or delete a ban | GET, PUT, PATCH, DELETE | Read, Update, Delete | Detail |
| `/api/bans/ban_user/` | Ban a user | POST | Create | Detail |
| `/api/bans/active_bans/` | List active bans | GET | Read | List |
| `/api/bans/unban_user/` | Unban a user | POST | Update | Detail |
| `/api/ban-appeals/` | List or create ban appeals | GET, POST | Read, Create | List |
| `/api/ban-appeals/<id>/` | Retrieve, update or delete a ban appeal | GET, PUT, PATCH, DELETE | Read, Update, Delete | Detail |
| `/api/notifications/` | List user's notifications | GET | Read | List |
| `/api/notifications/<id>/` | Retrieve a specific notification | GET | Read | Detail |
| `/api/notifications/mark_all_as_read/` | Mark all notifications as read | POST | Update | List |
| `/api/notifications/<id>/mark_as_read/` | Mark a specific notification as read | POST | Update | Detail |
| `/api/genres/` | Get all unique genres | GET | Read | List |

Note: The `<id>` in these URLs is typically an integer representing the primary key of the resource. However, for the profile endpoints, it might also accept a username string instead of an ID.

# Frameworks, Libraries, and Dependencies

The ZapTalk API is implemented in Python using Django and Django Rest Framework.
The following additional utilities, apps, and modules were also used:

## Django and Django Rest Framework

Django (5.1.1): A high-level Python web framework that encourages rapid development and clean, pragmatic design.
Django Rest Framework (3.15.2): A powerful and flexible toolkit for building Web APIs.

## Authentication and Authorization

dj-rest-auth (6.0.0): Provides a set of REST API endpoints for authentication and registration.
django-allauth (64.2.1): Integrated set of Django applications addressing authentication, registration, account management as well as 3rd party (social) account authentication.
djangorestframework-simplejwt (5.3.0): A JSON Web Token authentication plugin for Django REST Framework.

## Database and ORM

dj-database-url (2.2.0): Allows you to utilize the 12factor inspired DATABASE_URL environment variable to configure your Django application.
psycopg2-binary (2.9.9): PostgreSQL database adapter for Python.

## Image Handling

Pillow (10.4.0): Python Imaging Library that adds image processing capabilities to your Python interpreter.
cloudinary (1.41.0): Python and Django SDK for Cloudinary.
django-cloudinary-storage (0.3.0): Django package that provides Cloudinary storages for both media and static files as well as management commands for removing unnecessary files.

## Filtering

django-filter (24.3): Allows users to filter down a queryset based on a model's fields, displaying the form to let them do this.

## CORS

django-cors-headers (4.4.0): A Django application for handling the server headers required for Cross-Origin Resource Sharing (CORS).

## Server and Deployment

gunicorn (23.0.0): A Python WSGI HTTP Server for UNIX.
whitenoise (6.7.0): Allows your web app to serve its own static files, making it a self-contained unit that can be deployed anywhere without relying on nginx, Amazon S3 or any other external service.

## Environment and Settings

python-dotenv (1.0.0): Reads key-value pairs from a .env file and can set them as environment variables.

## Utilities

asgiref (3.8.1): ASGI specs, helper code, and adapters.
PyJWT (2.9.0): A Python library which allows you to encode and decode JSON Web Tokens (JWT).
sqlparse (0.5.1): A non-validating SQL parser module for Python.

These libraries and frameworks work together to provide a robust foundation for building a modern, responsive, and user-friendly Django REST API. They cover essential aspects such as database management, authentication, image handling, and deployment, enabling efficient development and maintenance of the application.

# Testing

### Manual testing

I added a superuser and a normal user in the Django Rest framework HTML interface.
When adding the views and serializers for each model I checked that I had the correct access from superuser/user and that the intended information was displayed.

Later when implementing the frontend I followed the user stories. I added the correct CRUD functionality for each of the functions needed for that single user story. After a function was confirmed to be working I marked that check box inside the user stories acceptance criteria.

Testing on the frontend revealed a number of bugs which had not been detected while testing the API in the django rest framework interface and also revealed extra functionality that I thought was needed when having a better view than just the wireframes. 

the following additional features were added as a result of front-end testing:

- likes_count and comments_count fields were added to the MovieSerializer. 
- Added a source to my avatar field inside my userprofile to be able to display the avatar
-Added a permission_classes = [AllowAny] to my Movieset when I decided that everyone could watch the movies without being logged in
- Added a ban/banappeal model
- Added a notifications model

### Automated tests

Nine unit tests were written for the `contacts` endpoint. These are in `contacts/tests.py`, and all passed:

- Test that the tribe administrator can list contacts for their tribe.
- Test that a tribe member with no admin status in the same tribe can list contacts.
- Test that an unauthenticated user cannot list contacts.
- Test that a tribe administrator can create a new contact for their tribe.
- Test that a tribe member without admin status cannot create a new contact.
- Test that an unauthenticated user cannot create a new contact.
- Test that a tribe administrator can delete a contact.
- Test that a tribe member without admin status cannot delete a contact.
- Test than an unauthenticated user cannot delete a contact.


### Python validation

Code errors and style issues were detected using the Pylance linter in VSCode, and immediately fixed throughout development.
All files containing custom Python code were then validated using the [Code Institute Python Linter](https://pep8ci.herokuapp.com/):


- `api/admin.py`: no errors found
- `api/apps.py`: no errors found
- `api/models.py`: no errors found
- `api/serializers.py`: no errors found
- `api/urls.py`: no errors found
- `api/utils.py`: no errors found
- `api/views.py`: no errors found

- `movieapi/asgi.py`: no errors found
- `movieapi/settings.py`: no errors found
- `movieapi/urls.py`: no errors found
- `movieapi/wsgi.py`: no errors found

### Resolved bugs


- The genre and search function had to be made case insensitive

- Added related_name to my userprofile model to be able to access it from my userserializer. with this I also had to change the serializer to go from using user.userprofile to user.profile

- I had to change filter_followed_likes to use followed_users self.request.user.profile.following.all() To then be able to sort movies from the users you're following and not display all liked movies

- Like wasn't defined, this was caused by a circular import. I had to change the generic relation to a string. likes = GenericRelation('Like')

- Updated models and serializers to match the movies.json file. of using the word Extract instead of Description


### Unresolved bugs

- The moviemodel isn't set up correctly to filter out the no-thumbnail movie objects. Currently it's filtering out if the movie has it's thumbnail value being null or ''. I'm now filtering this in the frontend, looking inside movies if it has a thumbnail attribute at all.

- The userid is different inside the userprofile and inside the comments. This was circumvented by adding a username to fetch instead.

- the way I'm fetching the movies is still poorly designed resulting in fetching 7500 movies on the home page when only looking for 3

## Deployment
The ZapTalk API is deployed to Heroku, using a Postgres database.
To duplicate deployment to Heroku, follow these steps:

- Fork or clone this repository in GitHub.
- You will need a Cloudinary account to host user profile images.
- Login to Cloudinary.
- Select the 'dashboard' option.
- Copy the value of the 'API Environment variable' from the part starting `cloudinary://` to the end. You may need to select the eye icon to view the full environment variable. Paste this value somewhere for safe keeping as you will need it shortly (but destroy after deployment).
- Log in to Heroku.
- Select 'Create new app' from the 'New' menu at the top right.
- Enter a name for the app and select the appropriate region.
- Select 'Create app'.
- Select 'Settings' from the menu at the top.
- Set up your own database
- Return to the Heroku dashboard.
- Select the 'settings' tab.
- Locate the 'reveal config vars' link and select.
- Enter the following config var names and values:
    - `CLOUDINARY_URL`: *your cloudinary URL as obtained above*
    - `DATABASE_URL`: *your database URL*
    - `SECRET_KEY`: *your secret key*
    - `ALLOWED_HOST`: *the url of your Heroku app (but without the `https://` prefix)*
- Select the 'Deploy' tab at the top.
- Select 'GitHub' from the deployment options and confirm you wish to deploy using GitHub. You may be asked to enter your GitHub password.
- Find the 'Connect to GitHub' section and use the search box to locate your repo.
- Select 'Connect' when found.
- Optionally choose the main branch under 'Automatic Deploys' and select 'Enable Automatic Deploys' if you wish your deployed API to be automatically redeployed every time you push changes to GitHub.
- Find the 'Manual Deploy' section, choose 'main' as the branch to deploy and select 'Deploy Branch'.
- Your API will shortly be deployed and you will be given a link to the deployed site when the process is complete.

## Credits

The following documentation was extensively referenced throughout development:
- The Code institute Moments walkthrough project
- [Django documentation](https://www.djangoproject.com)
- [Django Rest Framework documentation](https://www.django-rest-framework.org)
- [django-filter documentation](https://django-filter.readthedocs.io/en/stable/)
- [Python datetime documentation](https://docs.python.org/3/library/datetime.html)
- [dateutil documentation](https://dateutil.readthedocs.io/en/stable/index.html)
