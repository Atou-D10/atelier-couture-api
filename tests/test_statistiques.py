from datetime import date

import pytest

CLIENT = {"nom": "Diop", "prenom": "Fatou", "telephone": "771234567", "genre": "femme"}


@pytest.fixture
def oid(client, accueil_h, prestation):
    cid = client.post("/api/v1/clients", json=CLIENT, headers=accueil_h).json()["id"]
    corps = {"client_id": cid, "lignes": [{"type_vetement_id": prestation.id, "quantite": 2}]}
    return client.post("/api/v1/commandes", json=corps, headers=accueil_h).json()["id"]  # 70000


def test_droits_statistiques(client, accueil_h, tailleur_h, admin_h):
    routes = ["tableau-de-bord", "chiffre-affaires", "types-vetement", "top-clients", "impayes"]
    for r in routes:
        assert client.get(f"/api/v1/statistiques/{r}").status_code == 401
        assert client.get(f"/api/v1/statistiques/{r}", headers=accueil_h).status_code == 403
        assert client.get(f"/api/v1/statistiques/{r}", headers=tailleur_h).status_code == 403
        assert client.get(f"/api/v1/statistiques/{r}", headers=admin_h).status_code == 200


def test_tableau_de_bord(client, accueil_h, admin_h, oid):
    client.post(f"/api/v1/commandes/{oid}/paiements", json={"montant": 20000, "mode": "wave"},
                headers=accueil_h)
    t = client.get("/api/v1/statistiques/tableau-de-bord", headers=admin_h).json()
    assert t["chiffre_affaires_mois"] == 70000 and t["encaisse_mois"] == 20000
    assert t["nb_commandes_mois"] == 1 and t["reste_a_encaisser"] == 50000
    assert t["commandes_par_statut"]["en_attente"] == 1
    assert len(t["commandes_par_statut"]) == 8            # tous les statuts, même à 0
    assert t["commandes_par_statut"]["livree"] == 0


def test_annulee_exclue_du_ca(client, accueil_h, admin_h, oid):
    client.post(f"/api/v1/commandes/{oid}/statut", json={"statut": "annulee"}, headers=accueil_h)
    t = client.get("/api/v1/statistiques/tableau-de-bord", headers=admin_h).json()
    assert t["chiffre_affaires_mois"] == 0 and t["reste_a_encaisser"] == 0


def test_chiffre_affaires_periodes(client, admin_h, oid):
    r = client.get("/api/v1/statistiques/chiffre-affaires?granularite=mois", headers=admin_h).json()
    assert r["points"] == [{"periode": date.today().strftime("%Y-%m"),
                            "chiffre_affaires": 70000, "encaisse": 0}]
    r = client.get("/api/v1/statistiques/chiffre-affaires?date_debut=2020-01-01&date_fin=2020-01-31",
                   headers=admin_h).json()
    assert r["points"] == []                                # seulement les périodes avec activité


def test_dates_inversees_422(client, admin_h):
    r = client.get("/api/v1/statistiques/chiffre-affaires?date_debut=2026-02-01&date_fin=2026-01-01",
                   headers=admin_h)
    assert r.status_code == 422


def test_types_vetement_et_top_clients(client, admin_h, oid):
    t = client.get("/api/v1/statistiques/types-vetement", headers=admin_h).json()
    assert t[0]["nom"] == "Boubou" and t[0]["quantite_vendue"] == 2 and t[0]["chiffre_affaires"] == 70000
    c = client.get("/api/v1/statistiques/top-clients", headers=admin_h).json()
    assert c[0]["nb_commandes"] == 1 and c[0]["solde_du"] == 70000


def test_impayes_pagines(client, accueil_h, admin_h, oid):
    r = client.get("/api/v1/statistiques/impayes", headers=admin_h).json()
    assert r["total"] == 1 and r["items"][0]["solde"] == 70000
    client.post(f"/api/v1/commandes/{oid}/paiements", json={"montant": 70000, "mode": "wave"},
                headers=accueil_h)
    assert client.get("/api/v1/statistiques/impayes", headers=admin_h).json()["total"] == 0


def test_health_verifie_la_base(client):
    assert client.get("/health").json() == {"status": "ok"}