# -*- coding: utf-8 -*-

"""
<plugin key="FranceFuelPrice"
        name="Prix Carburant France"
        author="jjlf"
        version="2.1.0"
        wikilink=""
        externallink="https://www.prix-carburants.gouv.fr">

    <description>
        <h2>Prix Carburant France</h2>
        <p>Récupère le prix d'un carburant et recherche la station la moins chère dans un rayon donné.</p>
        <p>Filtre les stations fermées et les prix périmés (> 7 jours).</p>
    </description>

    <params>

        <param field="Mode1"
               label="ID Station"
               width="150px"
               required="true"
               default="35000023"/>

        <param field="Mode2"
               label="Carburant"
               width="150px">
            <options>
                <option label="Gazole" value="gazole" default="true"/>
                <option label="E85" value="e85"/>
                <option label="E10" value="e10"/>
                <option label="SP98" value="sp98"/>
            </options>
        </param>

        <param field="Mode3"
               label="Rayon"
               width="100px">
            <options>
                <option label="5 km" value="5"/>
                <option label="10 km" value="10" default="true"/>
                <option label="20 km" value="20"/>
                <option label="30 km" value="30"/>
                <option label="50 km" value="50"/>
            </options>
        </param>

        <param field="Mode4"
               label="Rafraichissement"
               width="100px">
            <options>
                <option label="15 min" value="15"/>
                <option label="30 min" value="30"/>
                <option label="60 min" value="60" default="true"/>
                <option label="120 min" value="120"/>
            </options>
        </param>

        <param field="Mode6"
               label="Debug"
               width="75px">
            <options>
                <option label="Non" value="0" default="true"/>
                <option label="Oui" value="1"/>
            </options>
        </param>

    </params>

</plugin>
"""

import Domoticz
import json
import math
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

BASE_URL = (
    "https://data.economie.gouv.fr/api/explore/v2.1/catalog/"
    "datasets/prix-des-carburants-en-france-flux-instantane-v2/records"
)

# Seuil au-delà duquel un prix est considéré périmé
PRICE_MAX_AGE_DAYS = 7


def parse_geom(geom):
    """Retourne (lat, lon) depuis un champ geom API, quel que soit son format."""
    if "lat" in geom and "lon" in geom:
        return geom["lat"], geom["lon"]
    # Format GeoJSON standard : coordinates = [lon, lat]
    return geom["coordinates"][1], geom["coordinates"][0]


def is_price_fresh(date_str):
    """
    Retourne True si la date ISO8601 fournie par l'API est dans les PRICE_MAX_AGE_DAYS derniers jours.
    Retourne True en cas de date absente/invalide (on ne rejette pas par défaut).
    """
    if not date_str:
        return True
    try:
        # L'API renvoie p.ex. "2024-05-28T10:32:00+02:00" ou "2024-05-28T10:32:00Z"
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        age = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
        return age <= timedelta(days=PRICE_MAX_AGE_DAYS)
    except Exception:
        return True


def is_station_open(station):
    """
    Retourne False si la station est marquée comme fermée dans l'API.
    Le champ 'fermeture_type' vaut 'D' (définitif) ou 'T' (temporaire).
    """
    fermeture = station.get("fermeture_type", "")
    if fermeture in ("D", "T"):
        return False
    return True


class BasePlugin:

    def __init__(self):
        self.lastLeader = ""
        self.counter = 0
        # Cache des dernières valeurs connues (résistance aux erreurs réseau)
        self.cache = {}

    def log(self, message):
        Domoticz.Log("FuelPrice: {}".format(message))

    def debug(self, message):
        if Parameters["Mode6"] == "1":
            Domoticz.Log("FuelPrice DEBUG: {}".format(message))

    def _update_device(self, unit, nValue, sValue):
        """
        Met à jour un device ET le cache.
        En cas d'erreur réseau, le cache permet de conserver la dernière valeur.
        """
        if unit in Devices:
            Devices[unit].Update(nValue=nValue, sValue=str(sValue))
        self.cache[unit] = (nValue, str(sValue))

    def _restore_from_cache(self):
        """Re-pousse les dernières valeurs connues si le cache est disponible."""
        if not self.cache:
            return
        self.log("Erreur réseau — conservation des dernières valeurs connues")
        for unit, (nv, sv) in self.cache.items():
            if unit in Devices:
                Devices[unit].Update(nValue=nv, sValue=sv)

    def onStart(self):

        self.log("Starting plugin v2.1.0")

        fuel = Parameters["Mode2"].upper()
        station_id = Parameters["Mode1"].strip()

        if 1 not in Devices:
            Domoticz.Device(
                Name="Prix {} station (€/L)".format(fuel),
                Unit=1,
                TypeName="Custom",
                Options={"Custom": "€/L"}
            ).Create()

        if 2 not in Devices:
            Domoticz.Device(
                Name="Meilleur {} rayon (€/L)".format(fuel),
                Unit=2,
                TypeName="Custom",
                Options={"Custom": "€/L"}
            ).Create()

        if 3 not in Devices:
            Domoticz.Device(
                Name="Station {} moins chère".format(fuel),
                Unit=3,
                TypeName="Text"
            ).Create()

        if 4 not in Devices:
            Domoticz.Device(
                Name="Top 3 {}".format(fuel),
                Unit=4,
                TypeName="Text"
            ).Create()

        # Device 5 : infos de la station configurée (adresse + statut)
        if 5 not in Devices:
            Domoticz.Device(
                Name="Station {} infos".format(fuel),
                Unit=5,
                TypeName="Text"
            ).Create()

        Domoticz.Heartbeat(20)
        self.log("Station configurée : {}".format(station_id))
        self.updatePrices()

    def onHeartbeat(self):

        refresh = int(Parameters["Mode4"])
        self.counter += 1

        if self.counter >= (refresh * 60) / 20:
            self.counter = 0
            self.updatePrices()

    def distance_km(self, lat1, lon1, lat2, lon2):

        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c

    def getJson(self, url):

        self.debug(url)

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Domoticz FuelPrice Plugin"}
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    def updatePrices(self):

        try:
            self._fetchAndUpdate()

        except Exception as e:
            Domoticz.Error("FuelPrice: {}".format(str(e)))
            self._restore_from_cache()

    def _fetchAndUpdate(self):

        station_id = Parameters["Mode1"].strip()
        fuel = Parameters["Mode2"]
        price_field = "{}_prix".format(fuel)
        date_field  = "{}_maj".format(fuel)

        # ── 1. Récupération de la station configurée ──────────────────────────

        url = (
            BASE_URL
            + "?where=id%3D"
            + urllib.parse.quote(station_id)
            + "&limit=1"
        )

        data = self.getJson(url)

        if data["total_count"] == 0:
            self.log("Station non trouvée : {}".format(station_id))
            return

        station = data["results"][0]
        lat, lon = parse_geom(station["geom"])

        # ── 2. Infos de la station (Device 5) ────────────────────────────────

        ville   = station.get("ville", "?")
        adresse = station.get("adresse", "?")
        nom     = station.get("nom", "")

        if is_station_open(station):
            statut = "ouverte"
        else:
            fermeture = station.get("fermeture_type", "")
            statut = "fermée définitivement" if fermeture == "D" else "fermée temporairement"

        label_station = "{} {} - {} ({})".format(
            nom, ville, adresse, statut
        ).strip()

        self._update_device(5, 0, label_station)
        self.log("Station : {}".format(label_station))

        # ── 3. Prix de la station configurée (Device 1) ───────────────────────

        price      = station.get(price_field)
        price_date = station.get(date_field)

        if price is None:
            self.log("{} non disponible pour la station {}".format(
                fuel.upper(), station_id
            ))
        elif not is_price_fresh(price_date):
            self.log("Prix {} périmé pour station {} (maj: {})".format(
                fuel.upper(), station_id, price_date
            ))
        else:
            self._update_device(1, 0, price)
            self.debug("Prix station : {} €/L (maj {})".format(price, price_date))

        # ── 4. Recherche dans le rayon ────────────────────────────────────────

        radius = Parameters["Mode3"]

        where = (
            "within_distance(geom,geom'POINT({} {})',{}km)"
        ).format(lon, lat, radius)

        radius_url = (
            BASE_URL
            + "?where="
            + urllib.parse.quote(where)
            + "&limit=100"
        )

        radius_data = self.getJson(radius_url)

        stations = []

        for s in radius_data["results"]:

            # Filtrer stations fermées
            if not is_station_open(s):
                self.debug("Station fermée ignorée : {} {}".format(
                    s.get("ville", ""), s.get("adresse", "")
                ))
                continue

            p = s.get(price_field)
            if p is None:
                continue

            # Filtrer prix périmés
            if not is_price_fresh(s.get(date_field)):
                self.debug("Prix périmé ignoré : {} {} (maj: {})".format(
                    s.get("ville", ""), s.get("adresse", ""), s.get(date_field)
                ))
                continue

            stations.append(s)

        if len(stations) == 0:
            self.log("Aucune station valide trouvée dans le rayon")
            return

        stations.sort(key=lambda x: x[price_field])

        # ── 5. Meilleur prix du rayon (Device 2) ─────────────────────────────

        best = stations[0]
        self._update_device(2, 0, best[price_field])

        leader = "{} - {}".format(best["ville"], best["adresse"])
        self._update_device(3, 0, leader)

        if leader != self.lastLeader:
            self.log("Nouvelle station la moins chère : {} ({:.3f} €/L)".format(
                leader, best[price_field]
            ))
            self.lastLeader = leader

        # ── 6. Top 3 (Device 4) ───────────────────────────────────────────────

        top3 = []

        for idx, s in enumerate(stations[:3], start=1):

            s_lat, s_lon = parse_geom(s["geom"])
            dist = self.distance_km(lat, lon, s_lat, s_lon)

            maj = s.get(date_field, "")
            age_str = ""
            if maj:
                try:
                    dt  = datetime.fromisoformat(maj.replace("Z", "+00:00"))
                    age = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
                    age_str = " (J-{})".format(age.days) if age.days > 0 else " (auj.)"
                except Exception:
                    pass

            top3.append(
                "{}. {} {:.1f}km {:.3f}{}".format(
                    idx,
                    s["ville"],
                    dist,
                    s[price_field],
                    age_str
                )
            )

        self._update_device(4, 0, " | ".join(top3))


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()
