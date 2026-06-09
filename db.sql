CREATE TABLE medicament (
    Id_m INTEGER PRIMARY KEY,
    Libelle TEXT NOT NULL,
    Prix_m REAL
);

CREATE TABLE pharmacie (
    Id_p INTEGER PRIMARY KEY,
    Nom_p TEXT NOT NULL
);

CREATE TABLE dispose_de (
    Id_m INTEGER,
    Id_p INTEGER,
    Quantite_d INTEGER,
    PRIMARY KEY (Id_m, Id_p),
    FOREIGN KEY (Id_m) REFERENCES medicament(Id_m),
    FOREIGN KEY (Id_p) REFERENCES pharmacie(Id_p)
);


INSERT INTO medicament (Id_m, Libelle, Prix_m) VALUES (1, 'Aspirine', 2.55);
INSERT INTO medicament (Id_m, Libelle, Prix_m) VALUES (2, 'Clamoxine', 5.5);
INSERT INTO medicament (Id_m, Libelle, Prix_m) VALUES (3, 'Sibelium', 15.5);
INSERT INTO medicament (Id_m, Libelle, Prix_m) VALUES (4, 'Zomig', 1.30);
INSERT INTO medicament (Id_m, Libelle, Prix_m) VALUES (5, 'Dafalgan', 7.25);
INSERT INTO medicament (Id_m, Libelle, Prix_m) VALUES (6, 'doliruthme', 6.2);
INSERT INTO pharmacie (Id_p, Nom_p) VALUES (1, 'Pharmacie_de_la_Rose');
