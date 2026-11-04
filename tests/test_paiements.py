from datetime import date, timedelta

import pytest

CLIENT = {"nom": "Diop", "prenom": "Fatou", "telephone": "771234567", "genre": "femme"}


@pytest.fixture
def oid(client, accueil_h, prestation):
    cid = client.post("/api/v1/clients", json=CLIENT, headers=accueil_h).json()["id"]
    corps = {"client_id": cid, "lignes": [{"type_vetement_id": prestation.id, "quantite": 2}]}
    return client.post("/api/v1/commandes", json=corps, headers=accueil_h).json()["id"]  # total 70000


def _payer(client, h, oid, montant, **extra):
    return client.post(f"/api/v1/commandes/{oid}/paiements",
                       json={"montant": montant, "mode": "wave", **extra}, headers=h)


def _commande(client, h, oid):
    return client.get(f"/api/v1/commandes/{oid}", headers=h).json()


def test_acompte_met_a_jour_solde(client, accueil_h, oid):
    assert _payer(client, accueil_h, oid, 20000, reference="W1").status_code == 201
    c = _commande(client, accueil_h, oid)
    assert c["montant_paye"] == 20000 and c["solde"] == 50000 and len(c["paiements"]) == 1


def test_paiement_superieur_au_solde_409_rg16(client, accueil_h, oid):
    assert _payer(client, accueil_h, oid, 70001).status_code == 409


def test_montant_nul_ou_negatif_422_rg16(client, accueil_h, oid):
    assert _payer(client, accueil_h, oid, 0).status_code == 422
    assert _payer(client, accueil_h, oid, -5).status_code == 422


def test_date_future_422_rg16(client, accueil_h, oid):
    demain = str(date.today() + timedelta(days=1))
    assert _payer(client, accueil_h, oid, 1000, date_paiement=demain).status_code == 422


def test_commande_annulee_409_rg16(client, accueil_h, oid):
    client.post(f"/api/v1/commandes/{oid}/statut", json={"statut": "annulee"}, headers=accueil_h)
    assert _payer(client, accueil_h, oid, 1000).status_code == 409


def test_droits_paiement(client, tailleur_h, accueil_h, admin_h, oid):
    assert _payer(client, tailleur_h, oid, 1000).status_code == 403
    assert _payer(client, accueil_h, oid, 1000).status_code == 201
    pid = client.get(f"/api/v1/commandes/{oid}/paiements", headers=tailleur_h).json()[0]["id"]
    assert client.delete(f"/api/v1/paiements/{pid}", headers=accueil_h).status_code == 403


def test_annulation_recalcule_rg17(client, accueil_h, admin_h, oid):
    _payer(client, accueil_h, oid, 20000)
    _payer(client, accueil_h, oid, 10000)
    pid = client.get(f"/api/v1/commandes/{oid}/paiements", headers=accueil_h).json()[0]["id"]
    assert client.delete(f"/api/v1/paiements/{pid}", headers=admin_h).status_code == 204
    c = _commande(client, accueil_h, oid)
    assert c["montant_paye"] == 10000 and c["solde"] == 60000
    assert client.delete("/api/v1/paiements/999", headers=admin_h).status_code == 404


def test_total_sous_le_paye_409_rg7(client, accueil_h, oid):
    _payer(client, accueil_h, oid, 60000)
    r = client.patch(f"/api/v1/commandes/{oid}", json={"remise": 20000}, headers=accueil_h)
    assert r.status_code == 409  # total 50000 < payé 60000


def test_annulation_avec_acompte_exige_commentaire_rg14(client, accueil_h, oid):
    _payer(client, accueil_h, oid, 10000)
    url = f"/api/v1/commandes/{oid}/statut"
    assert client.post(url, json={"statut": "annulee"}, headers=accueil_h).status_code == 422
    r = client.post(url, json={"statut": "annulee", "commentaire": "Remboursé en espèces"}, headers=accueil_h)
    assert r.status_code == 200