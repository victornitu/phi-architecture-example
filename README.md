# Example of Event-Driven Data Collection with the PHI Architecture

This project is an example of how to use the PHI Architecture to build Event-Driven Data Collection.
For more details, see the article ["Event-Driven Data Collection"][1] which offers in depth explanations.

## Requirements

To run this project, we advise to use Docker and Docker Compose.
It will avoid the trouble of installing all the required dependencies.
This projects uses Python 3.8, MongoDB, Kafka, and ZooKeeper.

## Quick start

The Makefile offers an extra layer on top of Docker Compose to simplify running the project.

Starting the project:
```bash
make start
``` 

Restarting the project and rebuild images if necessary
```bash
make restart
```

Display a list of the running services
```bash
make status
```

Stop the project and clean up environment
```bash
make stop
```

Clean/reset the database
```bash
make clean
```

Inspect logs of the service selected with the variable `SERVICE`
```bash
make inspect SERVICE=handler
```
The variable `SERVICE` must contain the name of service you wish to inspect.  
Here we inspect the service named `handler`.


[1]: https://medium.com/phi-skills/event-driven-data-collection-d662a7db52a5
