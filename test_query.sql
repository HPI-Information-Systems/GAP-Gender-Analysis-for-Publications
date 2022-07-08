SELECT Year, count(PublicationID) as count
FROM W_pub 
WHERE (Venue = "*SEM") AND (Position <> "1")
GROUP BY Year;