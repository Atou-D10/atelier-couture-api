def test_login_ok(client, admin):
    r = client.post("/api/v1/auth/login",
                    data={"username": "admin@test.sn", "password": "motdepasse1"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["expires_in"] > 0


def test_login_message_identique_rg23(client, admin):
    inconnu = client.post("/api/v1/auth/login", data={"username": "x@test.sn", "password": "motdepasse1"})
    faux_mdp = client.post("/api/v1/auth/login", data={"username": "admin@test.sn", "password": "mauvais123"})
    assert inconnu.status_code == faux_mdp.status_code == 401
    assert inconnu.json() == faux_mdp.json()


def test_me_sans_jeton_401(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_jeton_invalide_401(client):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer nimporte"})
    assert r.status_code == 401


def test_me_sans_donnee_sensible_rg21(client, admin_h):
    r = client.get("/api/v1/auth/me", headers=admin_h)
    assert r.status_code == 200
    assert "mot_de_passe" not in r.text and "hash" not in r.text


def test_compte_desactive_refuse_avec_jeton_valide_rg22(client, db, admin_h, admin):
    admin.actif = False
    db.commit()
    assert client.get("/api/v1/auth/me", headers=admin_h).status_code == 401
    r = client.post("/api/v1/auth/login",
                    data={"username": "admin@test.sn", "password": "motdepasse1"})
    assert r.status_code == 401