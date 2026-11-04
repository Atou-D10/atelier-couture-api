from datetime import date, timedelta


def test_scenario_demonstration_annexe_a(client, accueil_h, tailleur_h, admin_h, db):
    from app.models.type_vetement import TypeVetement

    # Catalogue de départ (en test, le seed n'est pas exécuté)
    boubou = TypeVetement(nom="Boubou", prix_base=35000, delai_jours=10, actif=True)
    pantalon = TypeVetement(nom="Pantalon", prix_base=12000, delai_jours=4, actif=True)
    db.add_all([boubou, pantalon])
    db.commit()

    # 1. Accueil crée Fatou Diop ; un doublon (autre écriture du numéro) est refusé
    r = client.post("/api/v1/clients", headers=accueil_h, json={
        "nom": "Diop", "prenom": "Fatou", "telephone": "77 123 45 67", "genre": "femme"})
    assert r.status_code == 201
    cid = r.json()["id"]
    r = client.post("/api/v1/clients", headers=accueil_h, json={
        "nom": "Autre", "prenom": "Client", "telephone": "771234567", "genre": "femme"})
    assert r.status_code == 409

    # 2. Le tailleur prend les mesures ; l'accueil reçoit 403
    url_m = f"/api/v1/clients/{cid}/mesures"
    r = client.post(url_m, headers=tailleur_h, json={"tour_poitrine": 98.5, "tour_taille": 82})
    assert r.status_code == 201
    mid = r.json()["id"]
    assert client.post(url_m, headers=accueil_h, json={"tour_cou": 38}).status_code == 403

    # 3. Commande : 2 boubous + 1 pantalon négocié, avec remise
    r = client.post("/api/v1/commandes", headers=accueil_h, json={
        "client_id": cid, "remise": 5000,
        "lignes": [{"type_vetement_id": boubou.id, "quantite": 2},
                   {"type_vetement_id": pantalon.id, "quantite": 1, "prix_unitaire": 10000}]})
    assert r.status_code == 201
    c = r.json()
    oid = c["id"]
    assert c["numero"] == f"CMD-{date.today().year}-{oid:05d}"
    assert c["montant_total"] == 75000
    assert c["date_livraison_prevue"] == str(date.today() + timedelta(days=10))
    assert c["mesure_id"] == mid

    # 4. Accueil tente « terminee » : refusé avec les statuts possibles
    url_s = f"/api/v1/commandes/{oid}/statut"
    r = client.post(url_s, headers=accueil_h, json={"statut": "terminee"})
    assert r.status_code == 409 and "Statuts possibles" in r.json()["detail"]

    # 5. Le tailleur fait avancer, avec aller-retour essayage / retouches
    for s in ["en_coupe", "en_couture", "essayage", "retouches", "essayage", "terminee"]:
        assert client.post(url_s, headers=tailleur_h, json={"statut": s}).status_code == 200
    histo = client.get(f"/api/v1/commandes/{oid}/historique", headers=accueil_h).json()
    assert len(histo) == 7 and histo[0]["ancien_statut"] is None

    # 6. Acompte Wave ; un paiement supérieur au solde est refusé
    url_p = f"/api/v1/commandes/{oid}/paiements"
    assert client.post(url_p, headers=accueil_h,
                       json={"montant": 30000, "mode": "wave"}).status_code == 201
    assert client.post(url_p, headers=accueil_h,
                       json={"montant": 50000, "mode": "wave"}).status_code == 409

    # 7. Livraison refusée : solde non payé
    url_l = f"/api/v1/commandes/{oid}/livraison/confirmer"
    assert client.post(url_l, headers=accueil_h, json={}).status_code == 409

    # 8. Solde encaissé, puis livraison confirmée
    assert client.post(url_p, headers=accueil_h,
                       json={"montant": 45000, "mode": "especes"}).status_code == 201
    r = client.post(url_l, headers=accueil_h, json={})
    assert r.status_code == 200
    assert r.json()["statut"] == "livree" and r.json()["solde"] == 0

    # 9. Admin : le tableau de bord reflète la commande ; l'accueil reçoit 403
    t = client.get("/api/v1/statistiques/tableau-de-bord", headers=admin_h).json()
    assert t["chiffre_affaires_mois"] == 75000 and t["encaisse_mois"] == 75000
    assert client.get("/api/v1/statistiques/tableau-de-bord", headers=accueil_h).status_code == 403

    # 10. Admin : impayés et retards (vides ici : tout est soldé et livré)
    assert client.get("/api/v1/statistiques/impayes", headers=admin_h).json()["total"] == 0
    assert client.get("/api/v1/commandes?en_retard=true", headers=admin_h).json()["total"] == 0