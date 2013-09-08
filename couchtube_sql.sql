DESCRIBE couchtube.series;

DESCRIBE couchtube.episodes;

ALTER TABLE episodes
ADD COLUMN ytId varchar(255);

ALTER TABLE episodes
MODIFY COLUMN series_title varchar(255) NOT NULL;
