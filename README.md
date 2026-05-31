# FuelPrice Domoticz Plugin

Plugin Domoticz permettant de récupérer le prix d'un carburant dans une station-service française à partir de l'API officielle du gouvernement français, et de trouver automatiquement la station la moins chère dans un rayon donné.

## Fonctionnalités

* Récupération du prix d'un carburant pour une station donnée.
* Recherche automatique de la station la moins chère dans un rayon configurable.
* Affichage du Top 3 des stations les moins chères avec distance et fraîcheur du prix.
* Filtrage automatique des stations fermées (définitivement ou temporairement).
* Filtrage des prix périmés (données de plus de 7 jours exclues).
* Affichage des informations et du statut de la station configurée.
* Conservation des dernières valeurs connues en cas d'indisponibilité de l'API.
* Utilisation de l'API officielle « Prix des carburants en France ».
* Choix du carburant directement depuis l'interface Domoticz.
* Rafraîchissement automatique configurable.
* Compatible avec les carburants suivants :

  * Gazole
  * E85
  * E10
  * SP98

---

## Source des données

Les données proviennent de l'API publique :

[Prix des carburants en France - Flux instantané v2](https://www.data.gouv.fr/datasets/prix-des-carburants-en-france-flux-instantane-v2-amelioree)

---

## Installation

### 1. Copier le plugin

Créer le répertoire :

```bash
domoticz/plugins/FuelPrice/
```

Puis copier les fichiers :

```text
plugin.py
README.md
```

dans ce répertoire.

### 2. Vérifier les droits

```bash
chmod 644 plugin.py
```

### 3. Redémarrer Domoticz

```bash
sudo systemctl restart domoticz
```

ou redémarrer votre instance Domoticz selon votre méthode habituelle.

### 4. Ajouter le matériel

Dans Domoticz :

```text
Réglages → Matériel
```

Sélectionner :

```text
Prix Carburant France
```

---

## Configuration

### ID Station

Identifiant unique de la station-service.

Exemple :

```text
35000023
```

### Carburant

Liste disponible :

* Gazole
* E85
* E10
* SP98

### Rayon

Rayon de recherche pour trouver la station la moins chère :

* 5 km
* 10 km (défaut)
* 20 km
* 30 km
* 50 km

### Rafraîchissement

Choix de la fréquence de mise à jour :

* 15 minutes
* 30 minutes
* 1 heure (défaut)
* 2 heures

### Debug

Active les logs détaillés dans Domoticz (URLs appelées, stations ignorées, prix périmés).

---

## Trouver l'ID d'une station

Le moyen le plus simple consiste à utiliser le site officiel du gouvernement :

[prix-carburants.gouv.fr](https://www.prix-carburants.gouv.fr)

### Étapes

1. Rechercher votre station-service.
2. Ouvrir la fiche de la station.
3. Récupérer l'identifiant présent dans l'URL.

### Exemple

URL de la station :

```text
https://www.prix-carburants.gouv.fr/station/35000023
```

L'ID de la station est :

```text
35000023
```

C'est cette valeur qu'il faut renseigner dans le champ :

```text
ID Station
```

### Exemple de configuration

| Paramètre        | Valeur   |
| ---------------- | -------- |
| ID Station       | 35000023 |
| Carburant        | E85      |
| Rayon            | 10 km    |
| Rafraîchissement | 1 heure  |

---

## Devices créés

Le plugin crée automatiquement 5 devices dans Domoticz :

| Unit | Nom                          | Type          | Description                                              |
|------|------------------------------|---------------|----------------------------------------------------------|
| 1    | Prix {carburant} station     | Custom Sensor | Prix en €/L de la station configurée                     |
| 2    | Meilleur {carburant} rayon   | Custom Sensor | Meilleur prix trouvé dans le rayon                       |
| 3    | Station {carburant} moins chère | Text       | Ville et adresse de la station la moins chère            |
| 4    | Top 3 {carburant}            | Text          | Les 3 stations les moins chères avec distance et âge du prix |
| 5    | Station {carburant} infos    | Text          | Adresse et statut (ouverte/fermée) de la station configurée |

### Exemple d'affichage du Top 3

```text
1. Pleumeleuc 0.0km 1.955 auj. | 2. Breteil 4.6km 1.955 J-2 | 3. Montauban-de-Bretagne 9.1km 1.959 J-1
```

---

## Filtres appliqués

### Stations fermées

Les stations marquées comme fermées définitivement (`D`) ou temporairement (`T`) dans l'API sont automatiquement exclues du classement. Le statut de la station configurée est affiché dans le Device 5.

### Prix périmés

Tout prix dont la date de mise à jour dépasse 7 jours est ignoré. Cela évite d'afficher des tarifs obsolètes dans le classement.

### Résilience réseau

En cas d'indisponibilité temporaire de l'API, le plugin conserve les dernières valeurs connues dans les devices au lieu de les vider.

---

## Journal Domoticz

Exemples de messages :

```text
FuelPrice: Starting plugin
FuelPrice: Station configurée : 35000023
FuelPrice: Station : Pleumeleuc - 2 Rue de l'Epinette (ouverte)
FuelPrice: Nouvelle station la moins chère : Pleumeleuc - 2 Rue de l'Epinette (1.955 €/L)
FuelPrice: Erreur réseau — conservation des dernières valeurs connues
```

---

## Structure du projet

```text
FuelPrice/
├── plugin.py
└── README.md
```

---

## Compatibilité

* Domoticz
* Framework Python Plugins
* Python 3.6+
* Linux
* Raspberry Pi

---

## Licence

MIT

---

## Remerciements

Merci à la Direction Générale de la Concurrence, de la Consommation et de la Répression des Fraudes (DGCCRF) et à la plateforme data.economie.gouv.fr pour la mise à disposition des données publiques sur les carburants.
