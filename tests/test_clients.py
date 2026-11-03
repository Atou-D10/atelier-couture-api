CLIENT = {"nom": "Diop", "prenom": "Fatou", "telephone": "77 123 45 67", "genre": "femme"}


def test_creation_normalise_telephone_rg1(client, accueil_h):
    r = client.post("/api/v1/clients", json=CLIENT, headers=accueil_h)
    assert r.status_code == 201
    assert r.json()["telephone"] == "771234567"


def test_doublon_telephone_409_rg1(client, accueil_h):
    client.post("/api/v1/clients", json=CLIENT, headers=accueil_h)
    r = client.post("/api/v1/clients", json={**CLIENT, "telephone": "771234567"}, headers=accueil_h)
    assert r.status_code == 409


def test_telephone_invalide_422(client, accueil_h):
    r = client.post("/api/v1/clients", json={**CLIENT, "telephone": "12ab"}, headers=accueil_h)
    assert r.status_code == 422


def test_patch_partiel_et_non_vidable(client, accueil_h):
    cid = client.post("/api/v1/clients", json=CLIENT, headers=accueil_h).json()["id"]
    r = client.patch(f"/api/v1/clients/{cid}", json={"adresse": "Dakar"}, headers=accueil_h)
    assert r.status_code == 200 and r.json()["adresse"] == "Dakar" and r.json()["nom"] == "Diop"
    assert client.patch(f"/api/v1/clients/{cid}", json={"nom": None}, headers=accueil_h).status_code == 422
    # garder son propre numéro n'est pas un doublon
    assert client.patch(f"/api/v1/clients/{cid}", json={"telephone": "771234567"}, headers=accueil_h).status_code == 200


def test_recherche_q_minimum_2_caracteres(client, accueil_h):
    client.post("/api/v1/clients", json=CLIENT, headers=accueil_h)
    assert client.get("/api/v1/clients?q=fa", headers=accueil_h).json()["total"] == 1
    assert client.get("/api/v1/clients?q=f", headers=accueil_h).status_code == 422
    assert client.get("/api/v1/clients?genre=homme", headers=accueil_h).json()["total"] == 0


def test_pagination_format(client, accueil_h):
    body = client.get("/api/v1/clients", headers=accueil_h).json()
    assert set(body) == {"items", "total", "limit", "offset"}
    assert body["limit"] == 20 and body["offset"] == 0


def test_suppression_reservee_admin(client, accueil_h, admin_h):
    cid = client.post("/api/v1/clients", json=CLIENT, headers=accueil_h).json()["id"]
    assert client.delete(f"/api/v1/clients/{cid}", headers=accueil_h).status_code == 403
    assert client.delete(f"/api/v1/clients/{cid}", headers=admin_h).status_code == 204
    assert client.get(f"/api/v1/clients/{cid}", headers=admin_h).status_code == 404


def test_resume_client_vide(client, accueil_h):
    cid = client.post("/api/v1/clients", json=CLIENT, headers=accueil_h).json()["id"]
    r = client.get(f"/api/v1/clients/{cid}/resume", headers=accueil_h).json()
    assert r["nb_commandes"] == 0 and r["solde_du"] == 0 and r["a_des_mesures"] is False