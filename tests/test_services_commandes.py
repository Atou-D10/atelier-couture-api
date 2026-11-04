from datetime import date

import pytest

from app.exceptions import ConflitError, InterditError, ValidationMetierError
from app.services import commandes as s

from app.models.enums import RoleUtilisateur as R, StatutCommande as St


def test_numero_rg5():
    assert s.formater_numero(2026, 17) == "CMD-2026-00017"
    assert s.formater_numero(2026, 123456) == "CMD-2026-123456"  # au-delà de 5 chiffres, pas de troncature


def test_somme_et_total_rg7():
    somme = s.somme_prestations([(2, 35000), (1, 10000)])
    assert somme == 80000
    assert s.calculer_total(somme, 5000) == 75000
    assert s.calculer_total(somme, 80000) == 0  # remise égale à la somme : permis


def test_remise_trop_grande_422_rg7():
    with pytest.raises(ValidationMetierError):
        s.calculer_total(1000, 1001)


def test_total_sous_le_paye_409_rg7():
    s.verifier_total_vs_paye(50000, 50000)  # égalité : permis
    with pytest.raises(ConflitError):
        s.verifier_total_vs_paye(49999, 50000)


def test_date_livraison_plus_long_delai_rg8():
    assert s.date_livraison_par_defaut(date(2026, 11, 3), [10, 4, 14]) == date(2026, 11, 17)


def test_date_livraison_avant_commande_422_rg8():
    s.verifier_date_livraison(date(2026, 11, 3), date(2026, 11, 3))  # même jour : permis
    with pytest.raises(ValidationMetierError):
        s.verifier_date_livraison(date(2026, 11, 2), date(2026, 11, 3))


def test_retard_rg11():
    class Fake:  # objet minimal : pas besoin de la base
        def __init__(self, prevue, statut):
            self.date_livraison_prevue, self.statut = prevue, statut

    from app.models.enums import StatutCommande as S
    hier, demain, auj = date(2026, 11, 2), date(2026, 11, 4), date(2026, 11, 3)
    assert s.est_en_retard(Fake(hier, S.en_couture), auj) is True
    assert s.est_en_retard(Fake(auj, S.en_couture), auj) is False   # le jour même, pas encore en retard
    assert s.est_en_retard(Fake(demain, S.en_couture), auj) is False
    assert s.est_en_retard(Fake(hier, S.livree), auj) is False
    assert s.est_en_retard(Fake(hier, S.annulee), auj) is False


def test_message_transition_interdite_exemple_enonce():
    with pytest.raises(ConflitError) as e:
        s.verifier_transition(St.en_attente, St.terminee, R.accueil, False, None)
    assert str(e.value) == (
        "Transition interdite : en_attente → terminee. Statuts possibles : annulee, en_coupe"
    )


def test_transitions_valides():
    s.verifier_transition(St.en_attente, St.en_coupe, R.tailleur, False, None)
    s.verifier_transition(St.essayage, St.retouches, R.tailleur, False, None)
    s.verifier_transition(St.retouches, St.essayage, R.tailleur, False, None)  # aller-retour
    s.verifier_transition(St.en_couture, St.terminee, R.tailleur, False, None)


def test_meme_statut_409_rg13():
    with pytest.raises(ConflitError):
        s.verifier_transition(St.en_coupe, St.en_coupe, R.accueil, False, None)


def test_livree_interdit_par_cette_route_rg13():
    with pytest.raises(ConflitError) as e:
        s.verifier_transition(St.terminee, St.livree, R.accueil, False, None)
    assert "confirmation de livraison" in str(e.value)


def test_statuts_finaux_sans_sortie():
    for final in (St.livree, St.annulee):
        with pytest.raises(ConflitError):
            s.verifier_transition(final, St.en_coupe, R.admin, False, None)


def test_tailleur_ne_peut_pas_annuler_403_rg14():
    with pytest.raises(InterditError):
        s.verifier_transition(St.en_attente, St.annulee, R.tailleur, False, None)


def test_annulation_avec_acompte_exige_commentaire_422_rg14():
    with pytest.raises(ValidationMetierError):
        s.verifier_transition(St.en_coupe, St.annulee, R.accueil, True, None)
    with pytest.raises(ValidationMetierError):
        s.verifier_transition(St.en_coupe, St.annulee, R.accueil, True, "   ")
    s.verifier_transition(St.en_coupe, St.annulee, R.accueil, True, "Remboursé en espèces")
    s.verifier_transition(St.en_coupe, St.annulee, R.accueil, False, None)  # sans acompte : libre