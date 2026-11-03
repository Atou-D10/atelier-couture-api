NOUVEAU = {"email": "n@test.sn", "nom_complet": "Nouveau",
           "mot_de_passe": "motdepasse1", "role": "accueil"}


def test_creation_201_sans_hash(client, admin_h):
    r = client.post("/api/v1/utilisateurs", json=NOUVEAU, headers=admin_h)
    assert r.status_code == 201
    assert "mot_de_passe" not in r.text


def test_email_doublon_409(client, admin_h):
    client.post("/api/v1/utilisateurs", json=NOUVEAU, headers=admin_h)
    assert client.post("/api/v1/utilisateurs", json=NOUVEAU, headers=admin_h).status_code == 409


def test_mot_de_passe_court_422_rg21(client, admin_h):
    r = client.post("/api/v1/utilisateurs", json={**NOUVEAU, "mot_de_passe": "123"}, headers=admin_h)
    assert r.status_code == 422


def test_droits_utilisateurs(client, accueil_h, tailleur_h):
    for h in (accueil_h, tailleur_h):
        assert client.get("/api/v1/utilisateurs", headers=h).status_code == 403
        assert client.post("/api/v1/utilisateurs", json=NOUVEAU, headers=h).status_code == 403
    assert client.get("/api/v1/utilisateurs").status_code == 401


def test_admin_ne_peut_pas_se_desactiver_rg24(client, admin_h, admin):
    r = client.patch(f"/api/v1/utilisateurs/{admin.id}", json={"actif": False}, headers=admin_h)
    assert r.status_code == 409


def test_admin_ne_peut_pas_perdre_son_role_rg24(client, admin_h, admin):
    r = client.patch(f"/api/v1/utilisateurs/{admin.id}", json={"role": "accueil"}, headers=admin_h)
    assert r.status_code == 409


def test_detail_404(client, admin_h):
    assert client.get("/api/v1/utilisateurs/999", headers=admin_h).status_code == 404