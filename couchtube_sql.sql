DESCRIBE couchtube.series;

DESCRIBE couchtube.episodes;

ALTER TABLE episodes
ADD COLUMN ytId varchar(255);

ALTER TABLE episodes
MODIFY COLUMN series_title varchar(255) NOT NULL;

ALTER TABLE series
MODIFY COLUMN year int(4) DEFAULT NULL;

SELECT *
FROM episodes;

DELETE FROM series;
DELETE FROM episodes;