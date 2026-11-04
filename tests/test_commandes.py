from datetime import date, timedelta

import pytest

from app.models.type_vetement import TypeVetement

CLIENT = {"nom": "Diop", "prenom": "Fatou", "telephone": "771234567", "genre": "femme"}


@pytest.fixture
def pantalon(db):
    p = TypeVetement(nom="Pantalon", prix_base=12000, delai_jours=4, actif=True)
    db.add(p)
    db.commit()
    return p


@pytest.fixture
def cid(client, accueil_h):
    return client.post("/api/v1/clients", json=CLIENT, headers=accueil_h).json()["id"]


def _commande(client, h, cid, prestation, **extra):
    corps = {"client_id": cid, "lignes": [{"type_vetement_id": prestation.id, "quantite": 2}]}
    corps.update(extra)
    return client.post("/api/v1/commandes", json=corps, headers=h)


def _statut(client, h, oid, statut, commentaire=None):
    return client.post(f"/api/v1/commandes/{oid}/statut",
                       json={"statut": statut, "commentaire": commentaire}, headers=h)


# ---------- Création : RG5 à RG9, RG15 ----------

def test_creation_calculs_rg5_rg6_rg7_rg8(client, accueil_h, cid, prestation, pantalon):
    r = _commande(client, accueil_h, cid, prestation, remise=5000,
                  lignes=[{"type_vetement_id": prestation.id, "quantite": 2},
                          {"type_vetement_id": pantalon.id, "prix_unitaire": 10000}])
    assert r.status_code == 201
    c = r.json()
    assert c["numero"] == f"CMD-{date.today().year}-{c['id']:05d}"          # RG5
    assert c["montant_total"] == 2 * 35000 + 10000 - 5000 == 75000          # RG6, RG7
    assert c["solde"] == 75000 and c["statut"] == "en_attente"
    assert c["date_livraison_prevue"] == str(date.today() + timedelta(days=10))  # RG8
    assert c["lignes"][0]["type_vetement_nom"] == "Boubou"


def test_creation_reservee_accueil_403(client, tailleur_h, cid, prestation):
    assert _commande(client, tailleur_h, cid, prestation).status_code == 403


def test_prestation_inactive_422_rg6(client, accueil_h, db, cid, prestation):
    prestation.actif = False
    db.commit()
    assert _commande(client, accueil_h, cid, prestation).status_code == 422


def test_remise_trop_grande_422_rg7(client, accueil_h, cid, prestation):
    assert _commande(client, accueil_h, cid, prestation, remise=999999).status_code == 422


def test_date_avant_commande_422_rg8(client, accueil_h, cid, prestation):
    hier = str(date.today() - timedelta(days=1))
    assert _commande(client, accueil_h, cid, prestation, date_livraison_prevue=hier).status_code == 422


def test_aucune_ligne_422(client, accueil_h, cid):
    r = client.post("/api/v1/commandes", json={"client_id": cid, "lignes": []}, headers=accueil_h)
    assert r.status_code == 422


def test_mesures_automatiques_et_autre_client_rg9(client, accueil_h, tailleur_h, cid, prestation):
    assert _commande(client, accueil_h, cid, prestation).json()["mesure_id"] is None
    mid = client.post(f"/api/v1/clients/{cid}/mesures", json={"tour_cou": 38}, headers=tailleur_h).json()["id"]
    assert _commande(client, accueil_h, cid, prestation).json()["mesure_id"] == mid
    autre = client.post("/api/v1/clients", json={**CLIENT, "telephone": "781112233"}, headers=accueil_h).json()["id"]
    assert _commande(client, accueil_h, autre, prestation, mesure_id=mid).status_code == 422


def test_historique_initial_rg15(client, accueil_h, cid, prestation):
    oid = _commande(client, accueil_h, cid, prestation).json()["id"]
    h = client.get(f"/api/v1/commandes/{oid}/historique", headers=accueil_h).json()
    assert len(h) == 1 and h[0]["ancien_statut"] is None and h[0]["nouveau_statut"] == "en_attente"


# ---------- Liste et détail ----------

def test_liste_filtres(client, accueil_h, cid, prestation):
    a = _commande(client, accueil_h, cid, prestation).json()
    _commande(client, accueil_h, cid, prestation)
    _statut(client, accueil_h, a["id"], "annulee")
    r = client.get("/api/v1/commandes?statut=annulee", headers=accueil_h).json()
    assert r["total"] == 1 and r["items"][0]["client_nom"] == "Fatou Diop"
    assert {"solde", "en_retard"} <= set(r["items"][0])
    assert client.get(f"/api/v1/commandes?numero={a['numero']}", headers=accueil_h).json()["total"] == 1
    assert client.get("/api/v1/commandes?en_retard=true", headers=accueil_h).json()["total"] == 0


def test_en_retard_rg11(client, accueil_h, db, cid, prestation):
    from app.models.commande import Commande
    oid = _commande(client, accueil_h, cid, prestation).json()["id"]
    db.get(Commande, oid).date_livraison_prevue = date.today() - timedelta(days=1)
    db.commit()
    assert client.get(f"/api/v1/commandes/{oid}", headers=accueil_h).json()["en_retard"] is True
    assert client.get("/api/v1/commandes?en_retard=true", headers=accueil_h).json()["total"] == 1


def test_detail_404(client, accueil_h):
    assert client.get("/api/v1/commandes/999", headers=accueil_h).status_code == 404


# ---------- Modification et lignes : RG7, RG10, RG12 ----------

def test_ajout_et_retrait_ligne_recalcule_rg7(client, accueil_h, cid, prestation, pantalon):
    c = _commande(client, accueil_h, cid, prestation).json()
    r = client.post(f"/api/v1/commandes/{c['id']}/lignes",
                    json={"type_vetement_id": pantalon.id}, headers=accueil_h)
    assert r.status_code == 201 and r.json()["montant_total"] == 82000
    ligne = r.json()["lignes"][1]["id"]
    r = client.delete(f"/api/v1/commandes/{c['id']}/lignes/{ligne}", headers=accueil_h)
    assert r.json()["montant_total"] == 70000


def test_derniere_ligne_409_rg10(client, accueil_h, cid, prestation):
    c = _commande(client, accueil_h, cid, prestation).json()
    r = client.delete(f"/api/v1/commandes/{c['id']}/lignes/{c['lignes'][0]['id']}", headers=accueil_h)
    assert r.status_code == 409
    assert client.delete(f"/api/v1/commandes/{c['id']}/lignes/999", headers=accueil_h).status_code == 404


def test_lignes_figees_hors_en_attente_409_rg10(client, accueil_h, tailleur_h, cid, prestation, pantalon):
    oid = _commande(client, accueil_h, cid, prestation).json()["id"]
    _statut(client, tailleur_h, oid, "en_coupe")
    r = client.post(f"/api/v1/commandes/{oid}/lignes", json={"type_vetement_id": pantalon.id}, headers=accueil_h)
    assert r.status_code == 409
    assert client.patch(f"/api/v1/commandes/{oid}", json={"notes": "ok"}, headers=accueil_h).status_code == 200


def test_remise_patch_422(client, accueil_h, cid, prestation):
    oid = _commande(client, accueil_h, cid, prestation).json()["id"]
    assert client.patch(f"/api/v1/commandes/{oid}", json={"remise": 999999}, headers=accueil_h).status_code == 422


def test_commande_annulee_figee_409_rg12(client, accueil_h, cid, prestation):
    oid = _commande(client, accueil_h, cid, prestation).json()["id"]
    assert _statut(client, accueil_h, oid, "annulee").status_code == 200
    assert client.patch(f"/api/v1/commandes/{oid}", json={"notes": "x"}, headers=accueil_h).status_code == 409


# ---------- Statuts : workflow, RG13, RG14, RG15 ----------

def test_transition_interdite_message_409(client, accueil_h, cid, prestation):
    oid = _commande(client, accueil_h, cid, prestation).json()["id"]
    r = _statut(client, accueil_h, oid, "terminee")
    assert r.status_code == 409
    assert r.json()["detail"] == "Transition interdite : en_attente → terminee. Statuts possibles : annulee, en_coupe"


def test_parcours_complet_et_historique_rg15(client, accueil_h, tailleur_h, cid, prestation):
    oid = _commande(client, accueil_h, cid, prestation).json()["id"]
    for s in ["en_coupe", "en_couture", "essayage", "retouches", "essayage", "terminee"]:
        assert _statut(client, tailleur_h, oid, s).status_code == 200
    h = client.get(f"/api/v1/commandes/{oid}/historique", headers=accueil_h).json()
    assert [x["nouveau_statut"] for x in h][-1] == "terminee" and len(h) == 7


def test_meme_statut_et_livree_409_rg13(client, accueil_h, tailleur_h, cid, prestation):
    oid = _commande(client, accueil_h, cid, prestation).json()["id"]
    assert _statut(client, tailleur_h, oid, "en_attente").status_code == 409
    for s in ["en_coupe", "en_couture", "terminee"]:
        _statut(client, tailleur_h, oid, s)
    assert _statut(client, accueil_h, oid, "livree").status_code == 409


def test_tailleur_ne_peut_pas_annuler_403_rg14(client, accueil_h, tailleur_h, cid, prestation):
    oid = _commande(client, accueil_h, cid, prestation).json()["id"]
    assert _statut(client, tailleur_h, oid, "annulee").status_code == 403


# ---------- RG4 ----------

def test_client_avec_commandes_non_supprimable_409_rg4(client, accueil_h, admin_h, cid, prestation):
    _commande(client, accueil_h, cid, prestation)
    assert client.delete(f"/api/v1/clients/{cid}", headers=admin_h).status_code == 409


def test_mesure_utilisee_non_supprimable_409_rg4(client, accueil_h, tailleur_h, cid, prestation):
    mid = client.post(f"/api/v1/clients/{cid}/mesures", json={"tour_cou": 38}, headers=tailleur_h).json()["id"]
    _commande(client, accueil_h, cid, prestation)
    assert client.delete(f"/api/v1/mesures/{mid}", headers=tailleur_h).status_code == 409


def test_resume_client_exclut_annulees(client, accueil_h, cid, prestation):
    a = _commande(client, accueil_h, cid, prestation).json()
    _commande(client, accueil_h, cid, prestation)
    _statut(client, accueil_h, a["id"], "annulee")
    r = client.get(f"/api/v1/clients/{cid}/resume", headers=accueil_h).json()
    assert r["nb_commandes"] == 1 and r["chiffre_affaires"] == 70000 and r["solde_du"] == 70000