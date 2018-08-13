# About
More stars - more commits! You can do it too, but you can't be bothered now, can you?

# MODELWRAPPER
An API+SDK+Storage+Threading framework for running machine learning models.

## Changelog
v1.0 Base upload
## TO-DO
* Rewrite README
* Add versioning to API
* Add GOLANG integration
* Set logger to use ConfigLoader
  * Also change logging level on the fly
* API Auto-tests
* Authentication
* Dashboard
* Model dump depth config
* Microservice composition option
* Service discovery
* Make container lightweight (get rid of CentOS and do the abose microservice thing)
* EVEN MORE
## Out of the box
Run [willdrug/modelwrapper](https://hub.docker.com/r/willdrug/modelwrapper/), while mounting the appropriate volumes:
* /models_handler/models
* /models_handler/dumps
* /redis/data
Upload your models to `/models_handler/models` volume and either issue a restart or, if you have set autorestart, issue a `DELETE` method to /service endpoint.

## Features
### API
Default is Flask-based REST API (as shown in start.py).
Provides a port into running tasks, changing current config and seeing stats.
Validates inbound params.

### Tasker
Default is Threaded, provides a way to register a function to be ran as a separate thread

### Config Loader
Uploads provided config (extending base class) into cache, making it persistent.
Refreshes online conf (like API port) upon restart.

### ModelWrapper
Provides basic FIT and PREDICT proxies, which can be ran as tasks.
You are welcome to write your own.

Models are uploaded as packages into /models dir (docker volume).
The only requirement is that they extend base classes provided.
Connectors are provided for most popular data sources.
Each model uploaded is stored on the shelf and you can restore to the previous versions (keep an eye on data to avoid reaching the same undesirable result after the next fit!)

# Credits and links
Docker image is available at [dockerhub](https://hub.docker.com/r/willdrug/modelwrapper/)

Credit to [Nario](https://github.com/Nario560/) for logger and modelwrapper base.