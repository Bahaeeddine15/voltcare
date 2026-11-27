
"""Serveur CSMS OCPP 1.6J pour VoltCare.

Lancement depuis la racine du projet :
    python simulator/csms.py

Serveur WebSocket :
    ws://localhost:9000/{code_borne}

Les événements OCPP sont transmis au module MQTT publisher.py.
"""

import asyncio
import logging

from datetime import datetime, timezone
from itertools import count
from urllib.parse import unquote

from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

from ocpp.routing import on
from ocpp.v16 import ChargePoint, call_result
from ocpp.v16.enums import Action

from config import BORNES, OCPP_PORT
from publisher import publier


# ============================================================
# CONFIGURATION
# ============================================================

LOG = logging.getLogger("voltcare.csms")

BORNES_CONNNUES = {borne.code for borne in BORNES}

# Identifiants uniques pendant l'execution du CSMS.
# La persistance apres redemarrage est hors du ticket.
COMPTEUR_TRANSACTIONS = count(1)


def utc_iso():
    """Retourne la date UTC au format attendu par OCPP."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


# ============================================================
# PUBLICATION MQTT
# ============================================================

async def mqtt_publier(type_message, code_borne, donnees):
    """Transmet un evenement au module MQTT sans bloquer OCPP."""

    async def envoyer():
        try:
            await asyncio.to_thread(
                publier,
                type_message,
                code_borne,
                donnees
            )

            LOG.info(
                "[%s] MQTT publie : %s",
                code_borne,
                type_message
            )

        except Exception:
            LOG.exception(
                "[%s] Echec publication MQTT : %s",
                code_borne,
                type_message
            )

    asyncio.create_task(envoyer())


# ============================================================
# BORNE OCPP 1.6
# ============================================================

class BorneOCPP(ChargePoint):

    def __init__(self, code_borne, connexion):
        super().__init__(code_borne, connexion)

        self.code_borne = code_borne

        # Transactions actives de cette connexion.
        self.transactions = {}

    # --------------------------------------------------------
    # 1. BOOT NOTIFICATION
    # --------------------------------------------------------

    @on(Action.boot_notification)
    async def boot(
        self,
        charge_point_vendor,
        charge_point_model,
        **kwargs
    ):

        LOG.info(
            "[%s] BootNotification : %s / %s",
            self.code_borne,
            charge_point_vendor,
            charge_point_model
        )

        await mqtt_publier(
            "boot",
            self.code_borne,
            {}
        )

        return call_result.BootNotification(
            current_time=utc_iso(),
            interval=60,
            status="Accepted"
        )

    # --------------------------------------------------------
    # 2. STATUS NOTIFICATION
    # --------------------------------------------------------

    @on(Action.status_notification)
    async def status(
        self,
        connector_id,
        error_code,
        status,
        info=None,
        **kwargs
    ):

        LOG.info(
            "[%s] StatusNotification : statut=%s erreur=%s",
            self.code_borne,
            status,
            error_code
        )

        if connector_id != 1:
            LOG.warning(
                "[%s] Connecteur non pris en charge : %s",
                self.code_borne,
                connector_id
            )

            return call_result.StatusNotification()

        donnees = {
            "connecteur_id": connector_id,
            "statut": status,
            "code_erreur": error_code
        }

        if info is not None:
            donnees["info"] = str(info)[:50]

        await mqtt_publier(
            "status",
            self.code_borne,
            donnees
        )

        return call_result.StatusNotification()

    # --------------------------------------------------------
    # 3. HEARTBEAT
    # --------------------------------------------------------

    @on(Action.heartbeat)
    async def heartbeat(self):

        LOG.info(
            "[%s] Heartbeat recu",
            self.code_borne
        )

        await mqtt_publier(
            "heartbeat",
            self.code_borne,
            {}
        )

        return call_result.Heartbeat(
            current_time=utc_iso()
        )

    # --------------------------------------------------------
    # 4. START TRANSACTION
    # --------------------------------------------------------

    @on(Action.start_transaction)
    async def start_transaction(
        self,
        connector_id,
        id_tag,
        meter_start,
        timestamp,
        **kwargs
    ):

        LOG.info(
            "[%s] StartTransaction : badge=%s compteur=%s Wh",
            self.code_borne,
            id_tag,
            meter_start
        )

        if connector_id != 1:
            LOG.warning(
                "[%s] StartTransaction refuse : connecteur=%s",
                self.code_borne,
                connector_id
            )

            return call_result.StartTransaction(
                transaction_id=0,
                id_tag_info={"status": "Invalid"}
            )

        if self.transactions:
            LOG.warning(
                "[%s] Transaction deja active",
                self.code_borne
            )

            return call_result.StartTransaction(
                transaction_id=0,
                id_tag_info={"status": "ConcurrentTx"}
            )

        # Identifiant unique pour cette execution du serveur.
        transaction_id = next(COMPTEUR_TRANSACTIONS)

        self.transactions[transaction_id] = id_tag

        await mqtt_publier(
            "session/start",
            self.code_borne,
            {
                "connecteur_id": connector_id,
                "transaction_id": transaction_id,
                "id_tag": id_tag,
                "compteur_debut_wh": meter_start
            }
        )

        LOG.info(
            "[%s] Transaction demarree : id=%s",
            self.code_borne,
            transaction_id
        )

        return call_result.StartTransaction(
            transaction_id=transaction_id,
            id_tag_info={"status": "Accepted"}
        )

    # --------------------------------------------------------
    # 5. METER VALUES
    # --------------------------------------------------------

    @on(Action.meter_values)
    async def meter_values(
        self,
        connector_id,
        meter_value,
        transaction_id=None,
        **kwargs
    ):

        LOG.info(
            "[%s] MeterValues : transaction=%s",
            self.code_borne,
            transaction_id
        )

        if connector_id != 1:
            LOG.warning(
                "[%s] MeterValues ignore : connecteur=%s",
                self.code_borne,
                connector_id
            )

            return call_result.MeterValues()

        correspondance = {
            "Energy.Active.Import.Register": (
                "energie_wh", "Wh"
            ),
            "Power.Active.Import": (
                "puissance_w", "W"
            ),
            "Voltage": (
                "tension_v", "V"
            ),
            "Current.Import": (
                "courant_a", "A"
            ),
            "Temperature": (
                "temperature_c", "Celsius"
            )
        }

        champs_requis = {
            "energie_wh",
            "puissance_w",
            "tension_v",
            "courant_a",
            "temperature_c"
        }

        for mesure in meter_value:

            donnees = {
                "connecteur_id": connector_id,
                "transaction_id": transaction_id
            }

            valeurs = mesure.get(
                "sampledValue",
                mesure.get("sampled_value", [])
            )

            for item in valeurs:

                nom = item.get(
                    "measurand",
                    "Energy.Active.Import.Register"
                )

                if nom not in correspondance:
                    continue

                champ, unite_attendue = correspondance[nom]

                try:
                    valeur = float(item["value"])
                except (ValueError, TypeError, KeyError):
                    LOG.warning(
                        "[%s] Valeur de mesure invalide : %s",
                        self.code_borne,
                        item
                    )
                    continue

                unite = item.get("unit", unite_attendue)

                if champ == "energie_wh" and unite == "kWh":
                    valeur *= 1000

                elif champ == "puissance_w" and unite == "kW":
                    valeur *= 1000

                elif unite != unite_attendue:
                    LOG.warning(
                        "[%s] Unite incorrecte : %s pour %s",
                        self.code_borne,
                        unite,
                        nom
                    )
                    continue

                if champ == "energie_wh":
                    donnees[champ] = int(valeur)
                else:
                    donnees[champ] = valeur

            absents = champs_requis - donnees.keys()

            if absents:
                LOG.warning(
                    "[%s] Mesure incomplete : %s",
                    self.code_borne,
                    sorted(absents)
                )
                continue

            await mqtt_publier(
                "meter",
                self.code_borne,
                donnees
            )

        return call_result.MeterValues()

    # --------------------------------------------------------
    # 6. STOP TRANSACTION
    # --------------------------------------------------------

    @on(Action.stop_transaction)
    async def stop_transaction(
        self,
        meter_stop,
        timestamp,
        transaction_id,
        reason=None,
        id_tag=None,
        **kwargs
    ):

        LOG.info(
            "[%s] StopTransaction : id=%s compteur=%s Wh",
            self.code_borne,
            transaction_id,
            meter_stop
        )

        badge = self.transactions.get(transaction_id)

        if badge is None:
            LOG.warning(
                "[%s] Transaction inconnue : %s",
                self.code_borne,
                transaction_id
            )

            return call_result.StopTransaction(
                id_tag_info={"status": "Invalid"}
            )

        if id_tag is not None and id_tag != badge:
            LOG.warning(
                "[%s] Badge incoherent pour transaction %s",
                self.code_borne,
                transaction_id
            )

            return call_result.StopTransaction(
                id_tag_info={"status": "Invalid"}
            )

        await mqtt_publier(
            "session/stop",
            self.code_borne,
            {
                "transaction_id": transaction_id,
                "id_tag": badge,
                "compteur_fin_wh": meter_stop,
                "raison": reason or "Local"
            }
        )

        del self.transactions[transaction_id]

        LOG.info(
            "[%s] Transaction terminee : id=%s",
            self.code_borne,
            transaction_id
        )

        return call_result.StopTransaction(
            id_tag_info={"status": "Accepted"}
        )


# ============================================================
# GESTION DES CONNEXIONS WEBSOCKET
# ============================================================

async def connexion_borne(ws):

    code_borne = unquote(
        ws.request.path.split("?", 1)[0].strip("/")
    )

    if (
        ws.subprotocol != "ocpp1.6"
        or code_borne not in BORNES_CONNNUES
    ):

        LOG.warning(
            "Connexion refusee : borne=%s protocole=%s",
            code_borne,
            ws.subprotocol
        )

        await ws.close(
            code=1008,
            reason="Borne ou protocole non autorise"
        )

        return

    LOG.info(
        "[%s] Borne connectee au CSMS",
        code_borne
    )

    borne = BorneOCPP(code_borne, ws)

    try:
        await borne.start()

    except ConnectionClosedOK:
        LOG.info(
            "[%s] Connexion fermee normalement",
            code_borne
        )

    except ConnectionClosedError as erreur:
        LOG.warning(
            "[%s] Connexion interrompue : %s",
            code_borne,
            erreur
        )

    except Exception:
        LOG.exception(
            "[%s] Erreur OCPP",
            code_borne
        )

    finally:
        LOG.info(
            "[%s] Borne deconnectee",
            code_borne
        )


# ============================================================
# DEMARRAGE DU SERVEUR
# ============================================================

async def main():

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    async with serve(
        connexion_borne,
        "127.0.0.1",
        OCPP_PORT,
        subprotocols=["ocpp1.6"]
    ):

        LOG.info(
            "CSMS VoltCare pret sur ws://localhost:%d/{code_borne}",
            OCPP_PORT
        )

        await asyncio.Future()


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        LOG.info("Arret du CSMS")
