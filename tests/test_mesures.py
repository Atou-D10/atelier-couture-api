CLIENT = {"nom": "Diop", "prenom": "Fatou", "telephone": "771234567", "genre": "femme"}


def _client_id(client, h):
    return client.post("/api/v1/clients", json=CLIENT, headers=h).json()["id"]


def test_creation_par_tailleur_201(client, accueil_h, tailleur_h):
    cid = _client_id(client, accueil_h)
    r = client.post(f"/api/v1/clients/{cid}/mesures", json={"tour_poitrine": 98.5}, headers=tailleur_h)
    assert r.status_code == 201
    assert r.json()["tour_poitrine"] == 98.5
    assert r.json()["date_prise"] is not None and r.json()["prise_par_id"]


def test_accueil_ne_peut_pas_prendre_mesures_403(client, accueil_h):
    cid = _client_id(client, accueil_h)
    r = client.post(f"/api/v1/clients/{cid}/mesures", json={"tour_cou": 38}, headers=accueil_h)
    assert r.status_code == 403


def test_aucune_mesure_422_rg2(client, accueil_h, tailleur_h):
    cid = _client_id(client, accueil_h)
    r = client.post(f"/api/v1/clients/{cid}/mesures", json={"notes": "vide"}, headers=tailleur_h)
    assert r.status_code == 422


def test_bornes_rg2(client, accueil_h, tailleur_h):
    cid = _client_id(client, accueil_h)
    url = f"/api/v1/clients/{cid}/mesures"
    assert client.post(url, json={"tour_cou": 300}, headers=tailleur_h).status_code == 201
    assert client.post(url, json={"tour_cou": 301}, headers=tailleur_h).status_code == 422
    assert client.post(url, json={"tour_cou": 0}, headers=tailleur_h).status_code == 422


def test_historique_et_derniere_rg3(client, accueil_h, tailleur_h):
    cid = _client_id(client, accueil_h)
    url = f"/api/v1/clients/{cid}/mesures"
    client.post(url, json={"tour_cou": 38, "date_prise": "2026-01-10"}, headers=tailleur_h)
    client.post(url, json={"tour_cou": 40, "date_prise": "2026-06-10"}, headers=tailleur_h)
    client.post(url, json={"tour_cou": 39, "date_prise": "2026-03-10"}, headers=tailleur_h)
    histo = client.get(url, headers=accueil_h).json()
    assert [m["tour_cou"] for m in histo] == [40, 39, 38]  # la plus récente d'abord
    assert client.get(f"{url}/derniere", headers=accueil_h).json()["tour_cou"] == 40


def test_derniere_404_sans_mesure(client, accueil_h):
    cid = _client_id(client, accueil_h)
    assert client.get(f"/api/v1/clients/{cid}/mesures/derniere", headers=accueil_h).status_code == 404


def test_patch_correction_et_422_si_tout_supprime(client, accueil_h, tailleur_h):
    cid = _client_id(client, accueil_h)
    mid = client.post(f"/api/v1/clients/{cid}/mesures", json={"tour_cou": 38}, headers=tailleur_h).json()["id"]
    r = client.patch(f"/api/v1/mesures/{mid}", json={"tour_cou": 39}, headers=tailleur_h)
    assert r.status_code == 200 and r.json()["tour_cou"] == 39
    r = client.patch(f"/api/v1/mesures/{mid}", json={"tour_cou": None}, headers=tailleur_h)
    assert r.status_code == 422
    assert client.get(f"/api/v1/mesures/{mid}", headers=accueil_h).json()["tour_cou"] == 39


def test_suppression_mesure_204(client, accueil_h, tailleur_h):
    cid = _client_id(client, accueil_h)
    mid = client.post(f"/api/v1/clients/{cid}/mesures", json={"tour_cou": 38}, headers=tailleur_h).json()["id"]
    assert client.delete(f"/api/v1/mesures/{mid}", headers=accueil_h).status_code == 403
    assert client.delete(f"/api/v1/mesures/{mid}", headers=tailleur_h).status_code == 204
    assert client.get(f"/api/v1/mesures/{mid}", headers=accueil_h).status_code == 404


def test_suppression_client_supprime_ses_mesures(client, accueil_h, tailleur_h, admin_h):
    cid = _client_id(client, accueil_h)
    mid = client.post(f"/api/v1/clients/{cid}/mesures", json={"tour_cou": 38}, headers=tailleur_h).json()["id"]
    assert client.delete(f"/api/v1/clients/{cid}", headers=admin_h).status_code == 204
    assert client.get(f"/api/v1/mesures/{mid}", headers=admin_h).status_code == 404