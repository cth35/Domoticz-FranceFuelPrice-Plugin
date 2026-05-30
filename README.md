# FuelPrice Domoticz Plugin

Plugin Domoticz permettant de récupérer le prix d'un carburant dans une station-service française à partir de l'API officielle du gouvernement français.

## Fonctionnalités

* Récupération du prix d'un carburant pour une station donnée.
* Utilisation de l'API officielle « Prix des carburants en France ».
* Choix du carburant directement depuis l'interface Domoticz.
* Rafraîchissement automatique configurable.
* Affichage du prix dans un capteur Domoticz.
* Compatible avec les carburants suivants :

  * Gazole
  * E85
  * E10
  * SP98

---

## Source des données

Les données proviennent de l'API publique :

**Prix des carburants en France - Flux instantané v2**

[data.economie.gouv.fr](https://data.economie.gouv.fr/?utm_source=chatgpt.com)

---

## Installation

### 1. Copier le plugin

Créer le répertoire :

```bash
domoticz/plugins/FuelPrice/
```

Puis copier le fichier :

```text
plugin.py
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
Fuel Price France
```

---

## Configuration

### ID Station

Identifiant unique de la station-service.

Exemple :

```text
35137001
```

### Carburant

Liste disponible :

* Gazole
* E85
* E10
* SP98

### Rafraîchissement

Choix de la fréquence de mise à jour :

* 15 minutes
* 30 minutes
* 1 heure
* 2 heures

---

## Trouver l'ID d'une station

Le moyen le plus simple consiste à utiliser le site officiel du gouvernement :

[prix-carburants.gouv.fr](https://www.prix-carburants.gouv.fr/?utm_source=chatgpt.com)

### Étapes

1. Rechercher votre station-service.
2. Ouvrir la fiche de la station.
3. Récupérer l'identifiant présent dans l'URL.

### Exemple

URL de la station :

```text
https://www.prix-carburants.gouv.fr/station/35137001
```

L'ID de la station est :

```text
35137001
```

C'est cette valeur qu'il faut renseigner dans le champ :

```text
ID Station
```

### Exemple de configuration

| Paramètre        | Valeur   |
| ---------------- | -------- |
| ID Station       | 35137001 |
| Carburant        | E85      |
| Rafraîchissement | 1 heure  |

Le plugin interrogera alors automatiquement l'API officielle pour récupérer le prix du carburant sélectionné. Les données du site prix-carburants.gouv.fr et de l'API gouvernementale proviennent de la même source officielle.

---

## Captures d'écran

### Configuration du matériel

![Configuration](docs/images/configuration.png)

---

### Device créé dans Domoticz

![Device](docs/images/device.png)

---

### Exemple de valeur affichée

![Valeur](docs/images/value.png)

---

### Historique du prix

![Historique](docs/images/history.png)

---

## Exemple de résultat

Pour la station :

```text
35137001
```

avec le carburant :

```text
E85
```

Le plugin affichera :

```text
0.789 €/L
```

---

## Structure du projet

```text
FuelPrice/
├── plugin.py
├── README.md
└── docs/
    └── images/
        ├── configuration.png
        ├── device.png
        ├── value.png
        └── history.png
```

---

## Journal Domoticz

Exemple de message :

```text
Fuel Price France: E85 = 0.789 €/L
```

---

## Compatibilité

* Domoticz
* Framework Python Plugins
* Linux
* Raspberry Pi

---

## Licence

MIT

---

## Remerciements

Merci à la Direction Générale de la Concurrence, de la Consommation et de la Répression des Fraudes (DGCCRF) et à la plateforme data.economie.gouv.fr pour la mise à disposition des données publiques sur les carburants.
