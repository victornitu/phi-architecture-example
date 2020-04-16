start:
	docker-compose up -d
restart:
	docker-compose up -d --build
stop:
	docker-compose down
status:
	docker-compose ps
inspect:
	docker-compose logs -f ${SERVICE}
clean:
	rm -rf data/db/*
