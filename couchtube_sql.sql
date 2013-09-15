DESCRIBE couchtube.series;

DESCRIBE couchtube.episodes;

ALTER TABLE episodes
ADD COLUMN ytId varchar(255);

ALTER TABLE series
ADD COLUMN ytLicensed int(5) DEFAULT 0;

ALTER TABLE series
ADD CONSTRAINT ytLicensed CHECK(ytLicensed>=0);

ALTER TABLE episodes
MODIFY COLUMN series_title varchar(255) NOT NULL;

ALTER TABLE series
MODIFY COLUMN year int(4) DEFAULT NULL;

SELECT *
FROM episodes
WHERE series_title="Grand Designs Abroad";

SELECT title, year, poster, episodes, ytcount, ytLicensed, 
	(episodes-ytLicensed)/episodes*100 as ppay, 
	ytcount/episodes as ytrep
FROM series
ORDER BY ytrep DESC;

UPDATE series
SET poster="http://ia.media-imdb.com/images/M/MV5BMTU3MzA3MjY2N15BMl5BanBnXkFtZTcwNDE5MDQ0OA@@._V1_SY317_CR12,0,214,317_.jpg"
WHERE title="Castle" AND year=2003;

SELECT *
FROM series;

SELECT title, season, episode, ytId, thumb
FROM episodes
WHERE series_title="Justified"
ORDER BY season, episode;

delete from episodes
where series_title="Justified";

delete from series
where title="Justified";
