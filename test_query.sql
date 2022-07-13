-- SELECT Publication.PublicationID, Author.AffiliationID, PublicationAuthor.DBLPName, PublicationAuthor.Position, Author.Gender, Publication.Year, Venue.Type, Country.CountryCode
-- FROM Publication
-- INDEXED BY publication_index 
-- INNER JOIN PublicationAuthor 
-- ON Publication.PublicationID = PublicationAuthor.PublicationID
-- INNER JOIN Author 
-- ON PublicationAuthor.DBLPName = Author.DBLPName
-- INNER JOIN Venue
-- ON Publication.VenueID = Venue.VenueID
-- WHERE (Country.CountryCode = "DE") AND (Author.Gender = "woman") AND (Publication.Year = "2018");

-- SELECT Year, count(DISTINCT PublicationID) as count
-- FROM W_pub 
-- INNER JOIN Pub_place
-- ON W_pub.AffiliationID == Pub_place.AffiliationID
-- WHERE (Venue = "SIGMOD Conference") AND (Pub_place.Country = "Germany") AND (Pub_place.Continent = "Europe") AND (Position = "1") AND (Gender = "woman")
-- GROUP BY Year;

-- EXPLAIN SELECT Year, count(DISTINCT Publication.PublicationID) as count
-- From Publication
-- INDEXED BY publication_index
-- INNER JOIN Venue
-- ON Publication.VenueID = Venue.VenueID
-- INNER JOIN PublicationAuthor
-- ON Publication.PublicationID = PublicationAuthor.PublicationID
-- INNER JOIN Author
-- ON PublicationAuthor.DBLPName = Author.DBLPName
-- INNER JOIN Affiliation
-- ON Author.AffiliationID = Affiliation.AffiliationID
-- INNER JOIN Country
-- ON Affiliation.CountryCode = Country.CountryCode
-- WHERE (Author.Gender = "woman") AND (Venue.Name = "SIGMOD Conference") AND (Country.DisplayName = "Germany") AND (Country.Continent = "Europe") AND (PublicationAuthor.Position = "1")

-- SELECT DISTINCT Type
-- FROM Venue

-- EXPLAIN SELECT Year, count(PublicationID) as count
-- FROM W_pub 
-- INNER JOIN Pub_place
-- ON W_pub.AffiliationID == Pub_place.AffiliationID
-- WHERE (Venue = "SIGMOD Conference") AND (Position = "1") AND (Gender = "woman")
-- GROUP BY Year;


-- SELECT PublicationID, count(DBLPName) as NumAuthors
-- FROM PublicationAuthor
-- GROUP BY PublicationID
-- ORDER BY NumAuthors DESC

DROP INDEX IF EXISTS all_together_index;

DROP TABLE IF EXISTS AllTogether;

CREATE TABLE AllTogether(PublicationID, PublicationType, AuthorID, Venue, AffiliationID, Position, Gender, Year, AuthorCount, Country, Continent);

INSERT INTO AllTogether
SELECT Publication.PublicationID, Publication.Type, Author.AuthorID, Venue.Name, Author.AffiliationID, PublicationAuthor.Position, Author.Gender, Publication.Year, Publication.AuthorCount, Country.DisplayName, Country.Continent
FROM Publication
INNER JOIN PublicationAuthor ON PublicationAuthor.PublicationID = Publication.PublicationID
INNER JOIN Author ON PublicationAuthor.DBLPName = Author.DBLPName
INNER JOIN Venue ON Publication.VenueID = Venue.VenueID
INNER JOIN Affiliation ON Author.AffiliationID = Affiliation.AffiliationID
INNER JOIN Country ON Affiliation.CountryCode = Country.CountryCode;

CREATE INDEX IF NOT EXISTS all_together_index ON AllTogether(PublicationID, PublicationType, AuthorID, Venue, AffiliationID, Position, Gender, Year, AuthorCount, Country, Continent);

CREATE UNIQUE INDEX IF NOT EXISTS publication_index ON Publication(PublicationID);
CREATE UNIQUE INDEX IF NOT EXISTS author_index ON Author(AuthorID);
CREATE UNIQUE INDEX IF NOT EXISTS affiliation_index ON Affiliation(AffiliationID);
CREATE UNIQUE INDEX IF NOT EXISTS venue_index ON Venue(VenueID);
CREATE INDEX IF NOT EXISTS publication_author_index ON PublicationAuthor(DBLPName);


-- SELECT PublicationID, count(DBLPName) as NumAuthors
-- FROM PublicationAuthor
-- GROUP BY PublicationID
-- ORDER BY NumAuthors ASC

-- Add the value of the column "NumAuthors" to the column "AuthorCount" from "Public", where the PublicationID is matching the PublicationID of the view "author_count_step"
-- UPDATE Publication
-- SET AuthorCount = author_count_step.NumAuthors
-- FROM author_count_step
-- WHERE Publication.PublicationID = author_count_step.PublicationID
