# -*- coding: utf-8 -*-

"""
<plugin key="FuelPrice"
        name="Fuel Price France"
        author="ChatGPT"
        version="1.0.0"
        wikilink=""
        externallink="https://data.economie.gouv.fr"
        >

    <description>
        <h2>Prix des carburants France</h2><br/>
        Récupère le prix d'un carburant pour une station donnée depuis
        l'API officielle du gouvernement français.
    </description>

    <params>

        <param field="Mode1"
               label="ID Station"
               width="200px"
               required="true"
               default="35137001"/>

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
               label="Rafraîchissement">
            <options>
                <option label="15 min" value="15"/>
                <option label="30 min" value="30"/>
                <option label="1 heure" value="60" default="true"/>
                <option label="2 heures" value="120"/>
            </options>
        </param>

        <param field="Mode6"
               label="Debug">
            <options>
                <option label="False" value="Normal" default="true"/>
                <option label="True" value="Debug"/>
            </options>
        </param>

    </params>

</plugin>
"""

import Domoticz
import json
import urllib.request
import urllib.error


class BasePlugin:

    def __init__(self):
        self.runCounter = 0
        self.heartbeatTarget = 360

    def onStart(self):

        Domoticz.Log("Fuel Price France plugin starting")

        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            DumpConfigToLog()

        if len(Devices) == 0:
            Domoticz.Device(
                Name="Prix carburant",
                Unit=1,
                TypeName="Custom",
                Options={"Custom": "€/L"}
            ).Create()

        try:
            refresh_minutes = int(Parameters["Mode3"])
        except Exception:
            refresh_minutes = 60

        #
        # Heartbeat Domoticz = 10 secondes
        #
        self.heartbeatTarget = max(
            1,
            int((refresh_minutes * 60) / 10)
        )

        Domoticz.Log(
            "Refresh interval: {} minute(s)".format(refresh_minutes)
        )

        self.updatePrice()

    def onStop(self):
        Domoticz.Log("Fuel Price France plugin stopped")

    def onHeartbeat(self):

        self.runCounter += 1

        if self.runCounter >= self.heartbeatTarget:
            self.runCounter = 0
            self.updatePrice()

    def updatePrice(self):

        station_id = Parameters["Mode1"].strip()
        fuel_type = Parameters["Mode2"].strip().lower()

        url = (
            "https://data.economie.gouv.fr/api/explore/v2.1/catalog/"
            "datasets/prix-des-carburants-en-france-flux-instantane-v2/"
            "records?where=id={}&limit=1"
        ).format(station_id)

        Domoticz.Log(
            "Requesting station {} ({})".format(
                station_id,
                fuel_type.upper()
            )
        )

        try:

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Domoticz FuelPrice Plugin"
                }
            )

            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.loads(
                    response.read().decode("utf-8")
                )

            if data.get("total_count", 0) == 0:
                Domoticz.Error(
                    "Station {} not found".format(station_id)
                )
                return

            station = data["results"][0]

            price_field = "{}_prix".format(fuel_type)
            date_field = "{}_maj".format(fuel_type)

            price = station.get(price_field)
            update_date = station.get(date_field)

            if price is None:
                Domoticz.Error(
                    "{} unavailable for station {}".format(
                        fuel_type.upper(),
                        station_id
                    )
                )

                if 1 in Devices:
                    Devices[1].Update(
                        nValue=0,
                        sValue="0"
                    )

                return

            Devices[1].Update(
                nValue=0,
                sValue=str(price)
            )

            Domoticz.Log(
                "{} = {} €/L (updated {})".format(
                    fuel_type.upper(),
                    price,
                    update_date
                )
            )

        except urllib.error.HTTPError as e:
            Domoticz.Error(
                "HTTP error {} : {}".format(
                    e.code,
                    e.reason
                )
            )

        except urllib.error.URLError as e:
            Domoticz.Error(
                "Network error : {}".format(e.reason)
            )

        except Exception as e:
            Domoticz.Error(
                "Unexpected error : {}".format(str(e))
            )


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


def DumpConfigToLog():

    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug(
                "'{}':'{}'".format(
                    x,
                    Parameters[x]
                )
            )

    Domoticz.Debug("Devices: {}".format(len(Devices)))

    for x in Devices:
        Domoticz.Debug(
            "Device {} - Name: '{}'".format(
                x,
                Devices[x].Name
            )
        )
