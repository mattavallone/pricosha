CREATE TABLE comments(
    c_id int(11) AUTO_INCREMENT PRIMARY KEY,
    commenter varchar(20) NOT NULL,
    item_id int(11) NOT NULL,
    text varchar(256) NOT NULL,
    is_public TINYINT(1) NOT NULL,
    FOREIGN KEY(item_id) REFERENCES contentitem(item_id),
	FOREIGN KEY(commenter) REFERENCES person(email));