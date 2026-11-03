def test_liste_actifs_par_defaut(client, accueil_h, prestation):
    assert len(client.get("/api/v1/catalogue", headers=accueil_h).json()) == 1


def test_creation_reservee_admin(client, accueil_h, admin_h):
    data = {"nom": "Veste", "prix_base": 40000, "delai_jours": 8}
    assert client.post("/api/v1/catalogue", json=data, headers=accueil_h).status_code == 403
    assert client.post("/api/v1/catalogue", json=data, headers=admin_h).status_code == 201
    assert client.post("/api/v1/catalogue", json=data, headers=admin_h).status_code == 409


def test_prix_negatif_422(client, admin_h):
    r = client.post("/api/v1/catalogue", json={"nom": "X", "prix_base": -5, "delai_jours": 3}, headers=admin_h)
    assert r.status_code == 422


def test_desactivation_masque_la_prestation(client, admin_h, prestation):
    pid = prestation.id
    client.patch(f"/api/v1/catalogue/{pid}", json={"actif": False}, headers=admin_h)
    assert client.get("/api/v1/catalogue", headers=admin_h).json() == []
    assert len(client.get("/api/v1/catalogue?actifs_seulement=false", headers=admin_h).json()) == 1


def test_detail_404(client, admin_h):
    assert client.get("/api/v1/catalogue/999", headers=admin_h).status_code == 404