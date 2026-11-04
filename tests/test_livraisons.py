from datetime import date, timedelta

import pytest

CLIENT = {"nom": "Diop", "prenom": "Fatou", "telephone": "771234567", "genre": "femme"}


@pytest.fixture
def oid(client, accueil_h, prestation):
    cid = client.post("/api/v1/clients", json=CLIENT, headers=accueil_h).json()["id"]
    corps = {"client_id": cid, "lignes": [{"type_vetement_id": prestation.id, "quantite": 2}]}
    return client.post("/api/v1/commandes", json=corps, headers=accueil_h).json()["id"]  # 70000


def _terminer(client, tailleur_h, oid):
    for s in ["en_coupe", "en_couture", "terminee"]:
        client.post(f"/api/v1/commandes/{oid}/statut", json={"statut": s}, headers=tailleur_h)


def _confirmer(client, h, oid, **corps):
    return client.post(f"/api/v1/commandes/{oid}/livraison/confirmer", json=corps, headers=h)


def test_domicile_sans_adresse_422_rg18(client, accueil_h, oid):
    r = client.put(f"/api/v1/commandes/{oid}/livraison",
                   json={"mode": "domicile", "date_prevue": str(date.today())}, headers=accueil_h)
    assert r.status_code == 422


def test_planifier_replanifier_rg18(client, accueil_h, oid):
    url = f"/api/v1/commandes/{oid}/livraison"
    assert client.get(url, headers=accueil_h).status_code == 404
    d1, d2 = date.today() + timedelta(days=3), date.today() + timedelta(days=6)
    r = client.put(url, json={"mode": "retrait_atelier", "date_prevue": str(d1)}, headers=accueil_h)
    assert r.status_code == 200
    r2 = client.put(url, json={"mode": "domicile", "adresse": "Dakar", "date_prevue": str(d2)},
                    headers=accueil_h)
    assert r2.json()["id"] == r.json()["id"]  # pas de seconde livraison
    c = client.get(f"/api/v1/commandes/{oid}", headers=accueil_h).json()
    assert c["date_livraison_prevue"] == str(d2) and c["livraison"]["mode"] == "domicile"
    assert len(client.get("/api/v1/livraisons", headers=accueil_h).json()) == 1


def test_confirmer_exige_terminee_409_rg19(client, accueil_h, oid):
    assert _confirmer(client, accueil_h, oid).status_code == 409


def test_confirmer_impaye_409_puis_solde_ok_rg19_rg20(client, accueil_h, tailleur_h, oid):
    _terminer(client, tailleur_h, oid)
    r = _confirmer(client, accueil_h, oid)
    assert r.status_code == 409 and "70000" in r.json()["detail"]
    client.post(f"/api/v1/commandes/{oid}/paiements", json={"montant": 70000, "mode": "wave"},
                headers=accueil_h)
    r = _confirmer(client, accueil_h, oid)
    assert r.status_code == 200
    c = r.json()
    assert c["statut"] == "livree" and c["solde"] == 0
    assert c["date_livraison_reelle"] == str(date.today())
    assert c["livraison"]["mode"] == "retrait_atelier"        # créée automatiquement
    assert c["livraison"]["statut"] == "livree" and c["livraison"]["date_effective"]


def test_autoriser_solde_impaye_rg19(client, accueil_h, tailleur_h, oid):
    _terminer(client, tailleur_h, oid)
    r = _confirmer(client, accueil_h, oid, autoriser_solde_impaye=True)
    assert r.status_code == 200 and r.json()["solde"] == 70000  # la dette reste visible
    h = client.get(f"/api/v1/commandes/{oid}/historique", headers=accueil_h).json()
    assert "impayé" in h[-1]["commentaire"]


def test_commande_livree_figee_rg12(client, accueil_h, tailleur_h, oid):
    _terminer(client, tailleur_h, oid)
    _confirmer(client, accueil_h, oid, autoriser_solde_impaye=True)
    r = client.put(f"/api/v1/commandes/{oid}/livraison",
                   json={"mode": "retrait_atelier", "date_prevue": str(date.today())}, headers=accueil_h)
    assert r.status_code == 409


def test_droits_livraison(client, tailleur_h, accueil_h, oid):
    corps = {"mode": "retrait_atelier", "date_prevue": str(date.today())}
    assert client.put(f"/api/v1/commandes/{oid}/livraison", json=corps, headers=tailleur_h).status_code == 403
    assert _confirmer(client, tailleur_h, oid).status_code == 403


def test_tournee_filtres_et_champs(client, accueil_h, oid):
    client.put(f"/api/v1/commandes/{oid}/livraison",
               json={"mode": "retrait_atelier", "date_prevue": str(date.today())}, headers=accueil_h)
    liste = client.get("/api/v1/livraisons?statut=planifiee", headers=accueil_h).json()
    assert len(liste) == 1
    assert {"numero_commande", "client_nom", "client_telephone", "solde_commande"} <= set(liste[0])
    assert client.get("/api/v1/livraisons?statut=livree", headers=accueil_h).json() == []