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

SELECT DISTINCT Type
FROM Venue

-- EXPLAIN SELECT Year, count(PublicationID) as count
-- FROM W_pub 
-- INNER JOIN Pub_place
-- ON W_pub.AffiliationID == Pub_place.AffiliationID
-- WHERE (Venue = "SIGMOD Conference") AND (Position = "1") AND (Gender = "woman")
-- GROUP BY Year;